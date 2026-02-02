"""
RAG Test Script - Demonstrates VectorDistance scoring
Run this to capture screenshot showing RAG retrieval with similarity scores.

Usage: python app/scripts/test_rag.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

# Sample knowledge base content for Banking International cards
KNOWLEDGE_BASE = [
    {
        "title": "BankGold Card Benefits",
        "category": "card_benefits",
        "content": "BankGold Card offers 4x points on dining worldwide, 3x points on travel purchases, no foreign transaction fees, and complimentary airport lounge access at select locations. Annual fee: $150."
    },
    {
        "title": "BankPlatinum Card Benefits", 
        "category": "card_benefits",
        "content": "BankPlatinum Card provides 5x points on dining worldwide, 4x points on travel and hotels, no foreign transaction fees, unlimited airport lounge access, travel insurance up to $500,000, and concierge service. Annual fee: $450."
    },
    {
        "title": "BankRewards Card Benefits",
        "category": "card_benefits",
        "content": "BankRewards Card earns 2x points on all purchases, 3x points on groceries, no foreign transaction fees, and basic travel insurance. Annual fee: $95."
    },
    {
        "title": "Airport Lounge Access Rules",
        "category": "lounge_rules",
        "content": "Banking International premium cardholders can access partner lounges worldwide. BankGold: 4 complimentary visits per year. BankPlatinum: Unlimited visits. Guest fees apply: $35 per guest. Children under 2 are free."
    },
    {
        "title": "Travel Insurance Coverage",
        "category": "travel_insurance",
        "content": "Banking International cards include travel insurance when travel is purchased with the card. Coverage includes: trip cancellation, lost luggage, medical emergencies abroad. BankPlatinum: Up to $500,000. BankGold: Up to $250,000. BankRewards: Up to $100,000."
    },
    {
        "title": "Foreign Transaction Policy",
        "category": "fx_policy",
        "content": "All Banking International premium cards have zero foreign transaction fees. Exchange rates are based on network rates at time of transaction. Dynamic currency conversion is available but not recommended - always pay in local currency."
    }
]


async def ingest_knowledge():
    """Ingest knowledge base into Cosmos DB with embeddings."""
    print("\n" + "="*70)
    print("STEP 1: INGESTING KNOWLEDGE BASE INTO COSMOS DB")
    print("="*70)
    
    from app.rag.ingest import get_cosmos_container, get_embedding_service, embed_texts
    
    container = get_cosmos_container()
    if not container:
        print("[FAIL] Could not connect to Cosmos DB")
        return False
    
    embedding_service = get_embedding_service()
    if not embedding_service:
        print("[FAIL] Could not initialize embedding service")
        return False
    
    print(f"[OK] Connected to Cosmos DB")
    print(f"[OK] Embedding service ready")
    print(f"\nIngesting {len(KNOWLEDGE_BASE)} documents...")
    
    for i, doc in enumerate(KNOWLEDGE_BASE):
        try:
            # Generate embedding
            embeddings = await embed_texts([doc["content"]])
            embedding = embeddings[0] if embeddings else []
            
            # Create document
            item = {
                "id": f"kb_{doc['category']}_{i}",
                "pk": "knowledge",
                "title": doc["title"],
                "category": doc["category"],
                "content": doc["content"],
                "embedding": embedding,
                "metadata": {
                    "source": "Banking International Knowledge Base",
                    "ingested_at": datetime.utcnow().isoformat(),
                    "embedding_dim": len(embedding)
                }
            }
            
            # Upsert to Cosmos DB
            container.upsert_item(item)
            print(f"  [{i+1}/{len(KNOWLEDGE_BASE)}] Ingested: {doc['title']}")
            
        except Exception as e:
            print(f"  [FAIL] Error ingesting {doc['title']}: {e}")
    
    print("\n[OK] Knowledge base ingestion complete")
    return True


def test_retrieval():
    """Test RAG retrieval with VectorDistance scores."""
    print("\n" + "="*70)
    print("STEP 2: TESTING RAG RETRIEVAL WITH VECTORDISTANCE")
    print("="*70)
    
    from app.rag.retriever import retrieve, generate_query_embedding_sync, get_cosmos_container
    
    # Test queries
    test_queries = [
        "What are the dining benefits of BankGold card?",
        "How much travel insurance does BankPlatinum provide?",
        "What are the airport lounge access rules?"
    ]
    
    container = get_cosmos_container()
    
    for query in test_queries:
        print(f"\n--- Query: {query} ---")
        
        # Generate embedding
        query_embedding = generate_query_embedding_sync(query)
        print(f"[OK] Query embedding generated (dim={len(query_embedding)})")
        
        # Execute vector search
        try:
            # Direct VectorDistance query for demonstration
            vector_query = """
            SELECT TOP 3 
                c.id, c.title, c.content,
                VectorDistance(c.embedding, @queryVector) as distance
            FROM c
            WHERE c.pk = 'knowledge'
            ORDER BY VectorDistance(c.embedding, @queryVector)
            """
            
            results = list(container.query_items(
                query=vector_query,
                parameters=[
                    {"name": "@queryVector", "value": query_embedding}
                ],
                enable_cross_partition_query=True
            ))
            
            print(f"[OK] VectorDistance query executed")
            print(f"\nResults with similarity scores:")
            print("-" * 50)
            
            for i, r in enumerate(results, 1):
                distance = r.get("distance", 0)
                similarity = 1 - distance  # Convert distance to similarity
                print(f"\n  [{i}] Title: {r.get('title', 'N/A')}")
                print(f"      VectorDistance: {distance:.6f}")
                print(f"      Similarity Score: {similarity:.4f} ({similarity*100:.1f}%)")
                print(f"      Content: {r.get('content', '')[:100]}...")
                
        except Exception as e:
            print(f"[FAIL] VectorDistance query failed: {e}")
            print("Falling back to manual similarity calculation...")
            
            # Fallback: manual calculation
            results = retrieve(query, k=3)
            print(f"\nFallback results:")
            for i, r in enumerate(results, 1):
                score = r.get("metadata", {}).get("relevance_score", 0)
                print(f"  [{i}] {r.get('title', 'N/A')} - Score: {score:.4f}")


def main():
    """Main test function."""
    print("\n" + "="*70)
    print("RAG SYSTEM TEST - VectorDistance Demonstration")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Step 1: Ingest knowledge base
    success = asyncio.run(ingest_knowledge())
    
    if not success:
        print("\n[FAIL] Ingestion failed, cannot proceed with retrieval test")
        return
    
    # Step 2: Test retrieval with VectorDistance
    test_retrieval()
    
    print("\n" + "="*70)
    print("RAG TEST COMPLETE")
    print("="*70)
    print("\nThis output demonstrates:")
    print("  1. Embedding generation using Azure OpenAI text-embedding-3-small")
    print("  2. Document storage in Cosmos DB with vector embeddings")
    print("  3. VectorDistance query execution with similarity scores")
    print("\nUse this console output for your 'RAG VectorDistance' screenshot.")


if __name__ == "__main__":
    main()
