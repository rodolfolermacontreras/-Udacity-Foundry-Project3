#!/usr/bin/env python3
"""
Updated Comprehensive System Health Check
- Includes Azure AI Foundry + Bing grounding check (merged from search_check)
- Validates: Azure OpenAI, Cosmos DB, Tools, State, Memory, Knowledge Base
"""

import sys
import os
import json
from datetime import datetime

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # This actually loads your .env file

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_environment():
    print("\n[CHECK] Environment Variables")
    print("-" * 40)
    required_vars = [
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_CHAT_DEPLOYMENT", "AZURE_OPENAI_EMBED_DEPLOYMENT",
        "AZURE_OPENAI_KEY", "COSMOS_ENDPOINT", "COSMOS_KEY",
        "COSMOS_DB", "COSMOS_CONTAINER", "COSMOS_PARTITION_KEY"
    ]
    missing = [v for v in required_vars if not os.environ.get(v)]
    for v in required_vars:
        print(f"{'[OK]' if v not in missing else '[MISSING]'} {v}")
    return len(missing) == 0

def check_azure_openai():
    print("\n[CHECK] Azure OpenAI Service")
    print("-" * 40)
    try:
        import asyncio
        from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
        from semantic_kernel.contents import ChatHistory

        chat = AzureChatCompletion(
            deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"]
        )

        embed = AzureTextEmbedding(
            deployment_name=os.environ["AZURE_OPENAI_EMBED_DEPLOYMENT"],
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"]
        )

        async def run_tests():
            # Use proper SK-compatible ChatHistory object
            chat_history = ChatHistory()
            chat_history.add_user_message("Reply with: pong")

            # Await the async call
            from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
            settings = PromptExecutionSettings(temperature=0, max_tokens=10)
            result = await chat.get_chat_message_contents(
                chat_history=chat_history,
                settings=settings
            )
            msg = result[0].content.strip()
            chat_ok = "pong" in msg.lower()
            print(f"{'[OK]' if chat_ok else '[FAIL]'} Chat: {msg}")

            # Test embedding generation
            vectors = await embed.generate_embeddings(["test"])
            dim = len(vectors[0]) if len(vectors) > 0 else 0
            emb_ok = dim > 256
            print(f"{'[OK]' if emb_ok else '[FAIL]'} Embedding: {dim} dimensions")

            return chat_ok and emb_ok

        return asyncio.run(run_tests())

    except Exception as e:
        print(f"[FAIL] Azure OpenAI check failed: {e}")
        return False

def check_cosmos_db():
    print("\n[CHECK] Cosmos DB Service")
    print("-" * 40)
    try:
        from azure.cosmos import CosmosClient
        client = CosmosClient(url=os.environ["COSMOS_ENDPOINT"], credential=os.environ["COSMOS_KEY"])
        db = client.get_database_client(os.environ["COSMOS_DB"])
        container = db.get_container_client(os.environ["COSMOS_CONTAINER"])
        items = list(container.query_items(query="SELECT TOP 1 * FROM c", enable_cross_partition_query=True))
        print(f"[OK] Cosmos DB connected (found {len(items)} item(s))")
        return True
    except Exception as e:
        print(f"[FAIL] Cosmos DB check failed: {e}")
        return False

def check_tools():
    print("\n[CHECK] Tool Integration")
    print("-" * 40)
    try:
        from app.tools.weather import WeatherTools
        from app.tools.fx import FxTools
        from app.tools.card import CardTools
        from app.tools.knowledge import KnowledgeTools
        from app.tools.search import SearchTools
        
        # Test Weather tool
        weather = WeatherTools().get_weather(48.8566, 2.3522)
        print(f"[OK] Weather: {weather.get('temperature', 'N/A')}C")
        
        # Test FX tool
        fx = FxTools().convert_fx(100, "USD", "EUR")
        print(f"[OK] FX: 100 USD = {fx.get('rates', {}).get('EUR', 'N/A')} EUR")
        
        # Test Card tool
        card = CardTools().recommend_card("5812", 100.0, "France")
        print(f"[OK] Card: {card.get('card', 'N/A')}")
        
        # Test Knowledge tool (synchronous)
        knowledge = KnowledgeTools().search_knowledge("BankGold dining")
        print(f"[OK] Knowledge: Found {len(knowledge.get('results', []))} results")
        
        # Test Search tool
        search = SearchTools().web_search("test", max_results=1)
        print(f"[OK] Search: {len(search)} result(s)")
        
        print("[OK] All tools working")
        return True
    except Exception as e:
        print(f"[FAIL] Tool check failed: {e}")
        return False

def check_grounding_search():
    print("\n[CHECK] Azure Grounding Search")
    print("-" * 40)
    try:
        from app.tools.search import SearchTools
        search = SearchTools()
        query = "best restaurants in Tokyo 2025"
        print(f"Querying Agent for: \"{query}\"")
        results = search.web_search(query, max_results=3)
        if not results or not isinstance(results, list):
            print("[FAIL] No results returned or invalid format")
            return False
        print(f"[OK] Received {len(results)} result(s):\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.get('title')}\n   URL: {r.get('url')}\n   {r.get('snippet')[:80]}...\n")
        return True
    except Exception as e:
        print(f"[FAIL] Grounding search check failed: {e}")
        return False

def check_state_management():
    print("\n[CHECK] State Management")
    print("-" * 40)
    try:
        from app.state import AgentState, Phase
        state = AgentState()
        state.advance()
        state.advance()
        state.advance()
        state.set_requirements({"destination": "Paris", "dates": "2026-06-01"})
        state.add_tool_call("weather", {"lat": 48.8566}, {"temp": 22})
        print("[OK] State management: Working")
        return True
    except Exception as e:
        print(f"[FAIL] State management check failed: {e}")
        return False

def check_memory_systems():
    print("\n[CHECK] Memory Systems")
    print("-" * 40)
    try:
        from app.memory import ShortTermMemory
        from app.long_term_memory import LongTermMemory
        stm = ShortTermMemory(max_items=5, max_tokens=1000)
        stm.add_conversation("user", "Hello")
        stm.add_conversation("assistant", "Hi there!")
        ltm = LongTermMemory(max_memories=1000, importance_threshold=0.3)
        ltm.add_memory("test", "Test memory", "test", 0.5)
        print("[OK] Short and long-term memory: Working")
        return True
    except Exception as e:
        print(f"[FAIL] Memory systems check failed: {e}")
        return False

def check_knowledge_base():
    print("\n[CHECK] Knowledge Base")
    print("-" * 40)
    try:
        from app.knowledge_base import search_card_benefits
        benefits = search_card_benefits("BankGold", "dining")
        print(f"[OK] Knowledge base: Found {len(benefits)} BankGold dining benefits")
        return True
    except Exception as e:
        print(f"[FAIL] Knowledge base check failed: {e}")
        return False

def main():
    print("Travel Concierge Agent - System Health Check")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    checks = [
        ("Environment Variables", check_environment),
        ("Azure OpenAI", check_azure_openai),
        ("Cosmos DB", check_cosmos_db),
        ("Tools", check_tools),
        ("Grounding Search", check_grounding_search),
        ("State Management", check_state_management),
        ("Memory Systems", check_memory_systems),
        ("Knowledge Base", check_knowledge_base)
    ]
    results = {}
    for name, fn in checks:
        print(f"\n[RUNNING] {name}...")
        results[name] = fn()
    print("\nHealth Check Summary")
    print("=" * 60)
    passed = sum(1 for r in results.values() if r)
    for name, result in results.items():
        print(f"{'[PASS]' if result else '[FAIL]'} {name}")
    print(f"\nOverall: {passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
