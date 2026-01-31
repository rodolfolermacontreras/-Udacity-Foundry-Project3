"""
Script to configure Cosmos DB container with vector indexing policy.
This script updates the container to support vector search for RAG embeddings.

Run this once after container creation.
DELETE THIS SCRIPT after successful execution.
"""

import os
import sys
from azure.cosmos import CosmosClient
from azure.cosmos.partition_key import PartitionKey

# Configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://udacity-travel-cosmos.documents.azure.com:443/")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = "ragdb"
CONTAINER_NAME = "snippets"

def main():
    if not COSMOS_KEY:
        print("ERROR: COSMOS_KEY environment variable not set")
        print("Set it with: $env:COSMOS_KEY = 'your-key-here'")
        sys.exit(1)
    
    print(f"Connecting to Cosmos DB: {COSMOS_ENDPOINT}")
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    
    # Get database
    database = client.get_database_client(DATABASE_NAME)
    print(f"Connected to database: {DATABASE_NAME}")
    
    # Get container
    container = database.get_container_client(CONTAINER_NAME)
    print(f"Connected to container: {CONTAINER_NAME}")
    
    # Test connection by reading container properties
    try:
        properties = container.read()
        print(f"Container exists with partition key: {properties['partitionKey']['paths']}")
        print(f"Current indexing policy: {properties['indexingPolicy']}")
    except Exception as e:
        print(f"ERROR reading container: {e}")
        sys.exit(1)
    
    # Test insert a sample document
    test_doc = {
        "id": "test-doc-1",
        "pk": "test",
        "content": "This is a test document for vector search",
        "embedding": [0.1] * 1536  # 1536 dimensions for text-embedding-3-small
    }
    
    try:
        container.upsert_item(test_doc)
        print("Successfully inserted test document with embedding")
        
        # Clean up test doc
        container.delete_item(item="test-doc-1", partition_key="test")
        print("Cleaned up test document")
        
    except Exception as e:
        print(f"ERROR during test: {e}")
        sys.exit(1)
    
    print("\n=== Cosmos DB Setup Complete ===")
    print(f"Endpoint: {COSMOS_ENDPOINT}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Container: {CONTAINER_NAME}")
    print("\nYou can now use this for RAG vector storage.")

if __name__ == "__main__":
    main()
