# app/rag/retriever.py
"""
RAG Retrieval Pipeline
Handles vector similarity search in Cosmos DB.
"""

from typing import List, Dict, Any, Optional
import os
import logging
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Cached clients
_cosmos_client: Optional[CosmosClient] = None
_container = None
_embedding_service = None


def get_embedding_service():
    """Get or create the embedding service."""
    global _embedding_service
    
    if _embedding_service is None:
        try:
            from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding
            
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION")
            embed_deployment = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
            
            if all([endpoint, api_key, api_version, embed_deployment]):
                _embedding_service = AzureTextEmbedding(
                    deployment_name=embed_deployment,
                    endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
                logger.info("[OK] Embedding service initialized for retrieval")
            else:
                logger.warning("[WARN] Missing Azure OpenAI config for embeddings")
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize embedding service: {e}")
    
    return _embedding_service


def get_cosmos_container():
    """Get or create the Cosmos DB container for RAG."""
    global _cosmos_client, _container
    
    if _container is None:
        try:
            endpoint = os.getenv("COSMOS_ENDPOINT")
            key = os.getenv("COSMOS_KEY")
            db_name = os.getenv("COSMOS_DB", "ragdb")
            container_name = os.getenv("COSMOS_CONTAINER", "snippets")
            
            if not endpoint or not key:
                logger.warning("[WARN] COSMOS_ENDPOINT and COSMOS_KEY not set")
                return None
            
            _cosmos_client = CosmosClient(endpoint, key)
            database = _cosmos_client.get_database_client(db_name)
            _container = database.get_container_client(container_name)
            
            logger.info(f"[OK] Connected to Cosmos DB for retrieval: {db_name}/{container_name}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Cosmos DB: {e}")
            return None
    
    return _container


async def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a search query.
    
    Args:
        query: Search query string
        
    Returns:
        Embedding vector
    """
    try:
        embedding_service = get_embedding_service()
        
        if embedding_service is None:
            logger.warning("Embedding service not available")
            return []
        
        result = await embedding_service.generate_embeddings([query])
        # Handle numpy array or list result
        if result is not None and len(result) > 0:
            embedding = result[0]
            # Convert numpy array to list if needed
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            return embedding
        return []
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate query embedding: {e}")
        return []


def generate_query_embedding_sync(query: str) -> List[float]:
    """
    Synchronous wrapper for query embedding generation.
    
    Args:
        query: Search query string
        
    Returns:
        Embedding vector
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(generate_query_embedding(query))


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def retrieve(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve relevant knowledge snippets using vector similarity search.
    
    Args:
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of relevant snippets with similarity scores
    """
    try:
        logger.info(f"[SEARCH] Retrieving documents for query: {query[:50]}...")
        
        container = get_cosmos_container()
        
        if container is None:
            logger.warning("[WARN] Cosmos DB not available for retrieval")
            return [{"error": "Database not available"}]
        
        # Generate query embedding
        query_embedding = generate_query_embedding_sync(query)
        
        if not query_embedding:
            logger.warning("[WARN] Could not generate query embedding, using text search")
            return text_search_fallback(query, k)
        
        logger.info(f"[OK] Generated query embedding (dim={len(query_embedding)})")
        
        # Try vector search with VectorDistance
        try:
            # Cosmos DB vector search query
            # Note: This requires Cosmos DB with vector search capability
            vector_query = """
            SELECT TOP @k 
                c.id, c.content, c.title, c.category, c.metadata,
                VectorDistance(c.embedding, @queryVector) as similarity
            FROM c
            WHERE c.pk = 'knowledge'
            ORDER BY VectorDistance(c.embedding, @queryVector)
            """
            
            results = list(container.query_items(
                query=vector_query,
                parameters=[
                    {"name": "@k", "value": k},
                    {"name": "@queryVector", "value": query_embedding}
                ],
                enable_cross_partition_query=True
            ))
            
            logger.info(f"[OK] Vector search returned {len(results)} results")
            
            return [
                {
                    "content": r.get("content", ""),
                    "title": r.get("title", ""),
                    "category": r.get("category", ""),
                    "metadata": {
                        **r.get("metadata", {}),
                        "relevance_score": 1 - r.get("similarity", 1),  # Convert distance to similarity
                        "source": r.get("metadata", {}).get("source", "knowledge_base")
                    }
                }
                for r in results
            ]
            
        except Exception as e:
            logger.warning(f"[WARN] Vector search failed, using fallback: {e}")
            return manual_vector_search(query_embedding, k)
        
    except Exception as e:
        logger.error(f"[ERROR] Retrieval error: {e}")
        return [{"error": str(e)}]


def manual_vector_search(query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
    """
    Manual vector search when VectorDistance is not available.
    Fetches all documents and computes similarity locally.
    
    Args:
        query_embedding: Query embedding vector
        k: Number of results to return
        
    Returns:
        List of relevant snippets with similarity scores
    """
    try:
        container = get_cosmos_container()
        
        if container is None:
            return []
        
        # Fetch all knowledge documents
        query = "SELECT * FROM c WHERE c.pk = 'knowledge'"
        documents = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"[CALC] Computing similarity for {len(documents)} documents")
        
        # Calculate similarity scores
        scored_docs = []
        for doc in documents:
            doc_embedding = doc.get("embedding", [])
            similarity = cosine_similarity(query_embedding, doc_embedding)
            scored_docs.append((similarity, doc))
        
        # Sort by similarity (descending)
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top-k results
        results = []
        for similarity, doc in scored_docs[:k]:
            results.append({
                "content": doc.get("content", ""),
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
                "metadata": {
                    **doc.get("metadata", {}),
                    "relevance_score": similarity,
                    "source": doc.get("metadata", {}).get("source", "knowledge_base")
                }
            })
        
        logger.info(f"[OK] Manual search returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"[ERROR] Manual vector search failed: {e}")
        return []


def text_search_fallback(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Fallback text search when embeddings are not available.
    
    Args:
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of matching snippets
    """
    try:
        container = get_cosmos_container()
        
        if container is None:
            return []
        
        # Simple text search using CONTAINS
        search_query = """
        SELECT TOP @k c.id, c.content, c.title, c.category, c.metadata
        FROM c
        WHERE c.pk = 'knowledge' 
        AND (CONTAINS(LOWER(c.content), @query) OR CONTAINS(LOWER(c.title), @query))
        """
        
        results = list(container.query_items(
            query=search_query,
            parameters=[
                {"name": "@k", "value": k},
                {"name": "@query", "value": query.lower()}
            ],
            enable_cross_partition_query=True
        ))
        
        logger.info(f"[OK] Text search returned {len(results)} results")
        
        return [
            {
                "content": r.get("content", ""),
                "title": r.get("title", ""),
                "category": r.get("category", ""),
                "metadata": {
                    **r.get("metadata", {}),
                    "relevance_score": 0.5,  # Default score for text search
                    "source": r.get("metadata", {}).get("source", "knowledge_base")
                }
            }
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"[ERROR] Text search failed: {e}")
        return []


if __name__ == "__main__":
    # Test retrieval
    print("[SEARCH] Testing RAG retrieval...")
    results = retrieve("BankGold dining benefits", k=3)
    for i, r in enumerate(results):
        print(f"\n{i+1}. {r.get('title', 'No title')}")
        print(f"   Score: {r.get('metadata', {}).get('relevance_score', 'N/A')}")
        print(f"   Content: {r.get('content', '')[:100]}...")
