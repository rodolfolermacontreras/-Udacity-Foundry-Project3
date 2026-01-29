# app/rag/ingest.py
"""
RAG Ingestion Pipeline
Handles embedding generation and storage in Cosmos DB vector store.
"""

from typing import List, Dict, Any, Optional
import os
import uuid
import logging
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
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
                logger.info("✅ Embedding service initialized")
            else:
                logger.warning("⚠️ Missing Azure OpenAI config for embeddings")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding service: {e}")
    
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
            partition_key = os.getenv("COSMOS_PARTITION_KEY", "/pk")
            
            if not endpoint or not key:
                logger.warning("⚠️ COSMOS_ENDPOINT and COSMOS_KEY not set")
                return None
            
            _cosmos_client = CosmosClient(endpoint, key)
            database = _cosmos_client.create_database_if_not_exists(id=db_name)
            
            # Create container with vector indexing policy
            _container = database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path=partition_key),
                indexing_policy={
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [{"path": "/*"}],
                    "excludedPaths": [{"path": "/embedding/*"}]
                }
            )
            
            logger.info(f"✅ Connected to Cosmos DB: {db_name}/{container_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Cosmos DB: {e}")
            return None
    
    return _container


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    try:
        embedding_service = get_embedding_service()
        
        if embedding_service is None:
            logger.warning("⚠️ Embedding service not available")
            return []
        
        logger.info(f"🔄 Generating embeddings for {len(texts)} texts")
        
        embeddings = []
        for text in texts:
            embedding = await embedding_service.generate_embeddings([text])
            if embedding:
                embeddings.append(embedding[0])
            else:
                embeddings.append([])
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
        
    except Exception as e:
        logger.error(f"❌ Failed to generate embeddings: {e}")
        return []


def embed_texts_sync(texts: List[str]) -> List[List[float]]:
    """
    Synchronous wrapper for embedding generation.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(embed_texts(texts))


def upsert_snippet(snippet: Dict[str, Any], embedding: List[float] = None) -> str:
    """
    Upsert a snippet with its embedding into Cosmos DB.
    
    Args:
        snippet: Dictionary containing snippet data (content, metadata, etc.)
        embedding: Pre-computed embedding vector (optional)
        
    Returns:
        Document ID of the upserted snippet
    """
    try:
        container = get_cosmos_container()
        
        if container is None:
            logger.warning("⚠️ Cosmos DB not available, skipping upsert")
            return ""
        
        # Generate ID if not provided
        doc_id = snippet.get("id", str(uuid.uuid4()))
        
        # Generate embedding if not provided
        if embedding is None and "content" in snippet:
            embeddings = embed_texts_sync([snippet["content"]])
            embedding = embeddings[0] if embeddings else []
        
        # Prepare document
        document = {
            "id": doc_id,
            "pk": snippet.get("pk", "knowledge"),
            "content": snippet.get("content", ""),
            "title": snippet.get("title", ""),
            "category": snippet.get("category", "general"),
            "embedding": embedding or [],
            "metadata": snippet.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Upsert to Cosmos DB
        container.upsert_item(document)
        
        logger.info(f"✅ Upserted snippet: {doc_id}")
        return doc_id
        
    except Exception as e:
        logger.error(f"❌ Failed to upsert snippet: {e}")
        return ""


def ingest_snippets(snippets: List[Dict[str, Any]]) -> List[str]:
    """
    Ingest multiple knowledge snippets into the vector database.
    
    Args:
        snippets: List of snippet dictionaries with content and metadata
        
    Returns:
        List of document IDs for ingested snippets
    """
    try:
        logger.info(f"📥 Ingesting {len(snippets)} snippets")
        
        # Generate embeddings for all contents
        contents = [s.get("content", "") for s in snippets]
        embeddings = embed_texts_sync(contents)
        
        # Upsert each snippet
        doc_ids = []
        for i, snippet in enumerate(snippets):
            embedding = embeddings[i] if i < len(embeddings) else None
            doc_id = upsert_snippet(snippet, embedding)
            if doc_id:
                doc_ids.append(doc_id)
        
        logger.info(f"✅ Successfully ingested {len(doc_ids)} snippets")
        return doc_ids
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return []


def ingest_knowledge_base():
    """
    Ingest the default knowledge base for the Travel Concierge.
    This includes card benefits, lounge rules, and travel policies.
    """
    knowledge_snippets = [
        {
            "content": "BankGold card offers 4x points on dining worldwide, 3x points on travel, and 2x points on gas stations and groceries. No foreign transaction fees. Basic travel insurance included.",
            "title": "BankGold Card Benefits",
            "category": "card_benefits",
            "pk": "knowledge",
            "metadata": {"card": "BankGold", "source": "Banking International"}
        },
        {
            "content": "BankPlatinum card offers 5x points on dining and travel, 3x points on gas and groceries. Includes Priority Pass lounge access, $200 annual travel credit, and Global Entry/TSA PreCheck credit.",
            "title": "BankPlatinum Card Benefits",
            "category": "card_benefits",
            "pk": "knowledge",
            "metadata": {"card": "BankPlatinum", "source": "Banking International"}
        },
        {
            "content": "BankRewards card offers 3x points on dining, travel, and streaming services. 1.5x points on all other purchases. Cell phone protection and travel delay insurance included.",
            "title": "BankRewards Card Benefits",
            "category": "card_benefits",
            "pk": "knowledge",
            "metadata": {"card": "BankRewards", "source": "Banking International"}
        },
        {
            "content": "Priority Pass lounge access allows cardholder plus 2 guests. Smart casual attire recommended. Access typically limited to 3 hours before departure. Capacity restrictions may apply during peak hours.",
            "title": "Airport Lounge Access Rules",
            "category": "lounge_rules",
            "pk": "knowledge",
            "metadata": {"source": "Banking International Lounge Policy"}
        },
        {
            "content": "Travel insurance covers up to $10,000 for trip cancellation, $500 for trip delays, $200 for baggage delays, and $50,000 for emergency medical coverage abroad.",
            "title": "Travel Insurance Coverage",
            "category": "travel_insurance",
            "pk": "knowledge",
            "metadata": {"source": "Banking International Travel Insurance"}
        },
        {
            "content": "For restaurant dining (MCC 5812), BankPlatinum earns 5x points and BankGold earns 4x points. Both cards have no foreign transaction fees for international dining.",
            "title": "Dining Benefits by Card",
            "category": "mcc_benefits",
            "pk": "knowledge",
            "metadata": {"mcc": "5812", "source": "Banking International"}
        },
        {
            "content": "For hotel stays (MCC 7011) and airlines (MCC 3000-3999), BankPlatinum earns 5x points with lounge access. BankGold earns 3x points. Both have no foreign transaction fees.",
            "title": "Travel Benefits by Card",
            "category": "mcc_benefits",
            "pk": "knowledge",
            "metadata": {"mcc": "7011", "source": "Banking International"}
        }
    ]
    
    return ingest_snippets(knowledge_snippets)


if __name__ == "__main__":
    # Run knowledge base ingestion
    print("🚀 Starting knowledge base ingestion...")
    doc_ids = ingest_knowledge_base()
    print(f"✅ Ingested {len(doc_ids)} documents")