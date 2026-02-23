# app/main.py - Travel Concierge Agent with Semantic Kernel
"""
Travel Concierge Agent with Semantic Kernel

This agent demonstrates:
- Semantic Kernel integration with Azure OpenAI and Cosmos DB
- Tool orchestration and state management
- Memory systems (short-term and long-term)
- RAG with knowledge base
- 8-phase state machine for robust processing
"""

import os
import json
import sys
import re
import asyncio
from typing import Dict, Any, Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from app.rag.retriever import retrieve
from app.synthesis import synthesize_to_tripplan
from app.state import AgentState, Phase
from app.memory import ShortTermMemory
from app.utils.config import validate_all_config
from app.utils.logger import setup_logger
from app.tools.weather import WeatherTools
from app.tools.fx import FxTools
from app.tools.search import SearchTools
from app.tools.card import CardTools
from app.tools.knowledge import KnowledgeTools
from app.filters import setup_kernel_filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logger("travel_agent")

# City coordinates for weather lookup
CITY_COORDINATES = {
    "paris": (48.8566, 2.3522),
    "tokyo": (35.6762, 139.6503),
    "london": (51.5074, -0.1278),
    "new york": (40.7128, -74.0060),
    "barcelona": (41.3851, 2.1734),
    "rome": (41.9028, 12.4964),
    "berlin": (52.5200, 13.4050),
    "sydney": (-33.8688, 151.2093),
    "dubai": (25.2048, 55.2708),
    "singapore": (1.3521, 103.8198),
}

# Country currency mapping
COUNTRY_CURRENCIES = {
    "france": "EUR",
    "germany": "EUR",
    "italy": "EUR",
    "spain": "EUR",
    "japan": "JPY",
    "uk": "GBP",
    "united kingdom": "GBP",
    "australia": "AUD",
    "uae": "AED",
    "dubai": "AED",
    "singapore": "SGD",
}

# System prompt for the travel concierge
SYSTEM_MESSAGE = """You are an expert AI Travel Concierge for Banking International's premium credit card members.

Your role is to help customers plan their trips by:
1. Understanding their travel requirements (destination, dates, card)
2. Providing relevant information using available tools
3. Recommending the best credit card benefits for their trip
4. Creating a structured travel plan

Available Tools:
- get_weather: Get weather forecast for a destination
- convert_fx: Convert currency for the destination
- web_search: Search for restaurants, attractions, and local information
- recommend_card: Get credit card recommendation based on spending categories
- get_card_recommendation: Get detailed card benefits from knowledge base
- search_knowledge: Search the knowledge base for card policies and benefits

Output Requirements:
- Always provide structured, validated responses
- Include source citations for any information
- Recommend the appropriate Banking International card based on the user's travel needs
- If data is unavailable, use null or "N/A" rather than making up information

Anti-hallucination Rules:
- Only use information from tool results or the knowledge base
- If a tool returns an error, acknowledge it and provide what information you can
- Do not fabricate specific prices, ratings, or details not provided by tools

Response Format:
Provide a comprehensive travel plan including weather, recommendations, card benefits, and next steps.
"""


def extract_requirements_from_input(user_input: str) -> dict:
    """
    Extract travel requirements from natural language input.
    
    Uses regex patterns to extract:
    - destination: city/country name
    - dates: travel date range
    - card: credit card type
    """
    requirements = {
        "destination": None,
        "dates": None,
        "card": "BankGold"  # Default card
    }
    
    input_lower = user_input.lower()
    
    # Extract destination - look for "to [city]" or known cities
    destination_patterns = [
        r"(?:to|visit|visiting|going to|trip to|travel to)\s+([A-Za-z\s]+?)(?:\s+from|\s+on|\s+in|\s+with|\s+starting|$|,|\.|!)",
        r"(?:in|at)\s+([A-Za-z]+)(?:\s+from|\s+on|\s+starting|$|,|\.|!)",
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            dest = match.group(1).strip()
            # Clean up common words
            dest = re.sub(r'\b(from|to|the|a|an|next|this)\b', '', dest, flags=re.IGNORECASE).strip()
            if dest and len(dest) > 2:
                requirements["destination"] = dest.title()
                break
    
    # Check for known cities if no pattern match
    if not requirements["destination"]:
        for city in CITY_COORDINATES.keys():
            if city in input_lower:
                requirements["destination"] = city.title()
                break
    
    # Extract dates - various patterns
    date_patterns = [
        r"from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})",  # 2026-06-01 to 2026-06-08
        r"(\w+\s+\d{1,2}(?:st|nd|rd|th)?)\s+(?:to|-)\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)",  # June 1st to June 8th
        r"(\w+\s+\d{1,2})-(\d{1,2})",  # July 10-17
        r"from\s+(\w+\s+\d{1,2})\s+to\s+(\w+\s+\d{1,2})",  # from June 1 to June 8
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                requirements["dates"] = f"{match.group(1)} to {match.group(2)}"
            break
    
    # Extract card type
    card_patterns = [
        r"(BankGold|BankPlatinum|BankRewards)",
        r"my\s+(gold|platinum|rewards)\s+card",
        r"with\s+(?:my\s+)?(gold|platinum|rewards)",
    ]
    
    for pattern in card_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            card = match.group(1).lower()
            if "gold" in card:
                requirements["card"] = "BankGold"
            elif "platinum" in card:
                requirements["card"] = "BankPlatinum"
            elif "rewards" in card:
                requirements["card"] = "BankRewards"
            break
    
    logger.info(f"[EXTRACT] Extracted requirements: {requirements}")
    return requirements


def create_kernel() -> Kernel:
    """
    Create and configure the Semantic Kernel instance.
    
    Sets up:
    - Azure OpenAI chat completion service
    - Azure OpenAI text embedding service
    - Tool plugins (WeatherTools, FxTools, SearchTools, CardTools, KnowledgeTools)
    """
    logger.info("[INIT] Creating Semantic Kernel...")
    
    kernel = Kernel()
    
    # Get Azure OpenAI configuration
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    embed_deployment = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
    
    # Add Azure Chat Completion service
    if endpoint and api_key:
        chat_service = AzureChatCompletion(
            deployment_name=chat_deployment,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        kernel.add_service(chat_service)
        logger.info(f"[OK] Added AzureChatCompletion: {chat_deployment}")
        
        # Add Azure Text Embedding service
        embedding_service = AzureTextEmbedding(
            deployment_name=embed_deployment,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        kernel.add_service(embedding_service)
        logger.info(f"[OK] Added AzureTextEmbedding: {embed_deployment}")
    else:
        logger.warning("[WARN] Azure OpenAI credentials not found")
    
    # Add tool plugins
    kernel.add_plugin(WeatherTools(), plugin_name="WeatherTools")
    kernel.add_plugin(FxTools(), plugin_name="FxTools")
    kernel.add_plugin(SearchTools(), plugin_name="SearchTools")
    kernel.add_plugin(CardTools(), plugin_name="CardTools")
    kernel.add_plugin(KnowledgeTools(), plugin_name="KnowledgeTools")
    
    logger.info("[OK] Registered all tool plugins")
    
    # Set up filters for logging and telemetry
    try:
        setup_kernel_filters(kernel)
        logger.info("[OK] Set up kernel filters")
    except Exception as e:
        logger.warning(f"[WARN] Could not set up filters: {e}")
    
    return kernel


def get_city_coordinates(destination: str) -> tuple:
    """Get coordinates for a city."""
    dest_lower = destination.lower()
    
    # Direct match
    if dest_lower in CITY_COORDINATES:
        return CITY_COORDINATES[dest_lower]
    
    # Partial match
    for city, coords in CITY_COORDINATES.items():
        if city in dest_lower or dest_lower in city:
            return coords
    
    # Default to Paris if unknown
    return CITY_COORDINATES["paris"]


def get_target_currency(destination: str) -> str:
    """Get the local currency for a destination."""
    dest_lower = destination.lower()
    
    # Check country mapping
    for country, currency in COUNTRY_CURRENCIES.items():
        if country in dest_lower:
            return currency
    
    # City-based mapping
    city_currencies = {
        "paris": "EUR",
        "tokyo": "JPY",
        "london": "GBP",
        "barcelona": "EUR",
        "rome": "EUR",
        "berlin": "EUR",
        "sydney": "AUD",
        "dubai": "AED",
        "singapore": "SGD",
        "new york": "USD",
    }
    
    for city, currency in city_currencies.items():
        if city in dest_lower:
            return currency
    
    return "EUR"  # Default


async def execute_tools(kernel: Kernel, state: AgentState, requirements: dict) -> dict:
    """
    Execute all relevant tools for the travel plan.
    
    Returns a dictionary of tool results.
    """
    tool_results = {}
    destination = requirements.get("destination", "Paris")
    card = requirements.get("card", "BankGold")
    
    # 1. Get weather
    try:
        lat, lon = get_city_coordinates(destination)
        weather_tool = WeatherTools()
        weather_data = weather_tool.get_weather(lat, lon)
        tool_results["weather"] = weather_data
        state.add_tool_call("weather", weather_data)
        logger.info(f"[OK] Weather data retrieved for {destination}")
    except Exception as e:
        logger.warning(f"[WARN] Weather tool error: {e}")
        state.add_tool_call("weather", error=str(e))
    
    # 2. Get currency exchange
    try:
        target_currency = get_target_currency(destination)
        fx_tool = FxTools()
        fx_data = fx_tool.convert_fx(100.0, "USD", target_currency)
        tool_results["fx"] = fx_data
        state.add_tool_call("fx", fx_data)
        logger.info(f"[OK] FX data retrieved: USD to {target_currency}")
    except Exception as e:
        logger.warning(f"[WARN] FX tool error: {e}")
        state.add_tool_call("fx", error=str(e))
    
    # 3. Search for restaurants/attractions
    try:
        search_tool = SearchTools()
        search_results = search_tool.web_search(f"best restaurants in {destination}", 5)
        tool_results["search"] = search_results
        state.add_tool_call("search", search_results)
        logger.info(f"[OK] Search results retrieved for {destination}")
    except Exception as e:
        logger.warning(f"[WARN] Search tool error: {e}")
        state.add_tool_call("search", error=str(e))
    
    # 4. Get card recommendation
    try:
        card_tool = CardTools()
        card_data = card_tool.recommend_card("5812", 100.0, destination)  # 5812 = restaurants
        tool_results["card"] = card_data
        state.add_tool_call("card", card_data)
        logger.info(f"[OK] Card recommendation retrieved")
    except Exception as e:
        logger.warning(f"[WARN] Card tool error: {e}")
        state.add_tool_call("card", error=str(e))
    
    # 5. Get knowledge base info
    try:
        knowledge_tool = KnowledgeTools()
        knowledge_data = knowledge_tool.get_card_recommendation("5812", destination)
        tool_results["knowledge"] = knowledge_data
        state.add_tool_call("knowledge", knowledge_data)
        logger.info(f"[OK] Knowledge base info retrieved")
    except Exception as e:
        logger.warning(f"[WARN] Knowledge tool error: {e}")
        state.add_tool_call("knowledge", error=str(e))
    
    return tool_results


async def run_request(user_input: str) -> str:
    """
    Main entry point for the travel agent.
    
    Implements the complete agent workflow:
    1. Extract requirements from user input
    2. Create and configure the kernel
    3. Initialize agent state
    4. Execute the agent workflow through all phases
    5. Return the synthesized travel plan as JSON
    """
    try:
        logger.info("=" * 60)
        logger.info(f"[START] Processing request: {user_input[:50]}...")
        
        # Initialize state
        state = AgentState()
        memory = ShortTermMemory()
        
        # Phase 1: Init
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        memory.add_conversation("user", user_input)
        
        # Phase 2: ClarifyRequirements
        state.advance()
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        
        requirements = extract_requirements_from_input(user_input)
        state.set_requirements(requirements)
        
        if not requirements.get("destination"):
            # Need clarification
            state.add_clarification_question("What destination are you planning to visit?")
            requirements["destination"] = "Paris"  # Default for demo
            logger.info("[WARN] No destination found, defaulting to Paris")
        
        # Phase 3: PlanTools
        state.advance()
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        
        # Create kernel
        kernel = create_kernel()
        
        # Phase 4: ExecuteTools
        state.advance()
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        
        tool_results = await execute_tools(kernel, state, requirements)
        
        # Phase 5: AnalyzeResults
        state.advance()
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        
        analysis = {
            "tools_executed": len(state.tools_called),
            "tools_with_errors": len(state.tool_errors),
            "data_quality": "good" if len(state.tool_errors) < 2 else "partial"
        }
        state.set_analysis_results(analysis)
        
        # Phase 6: ResolveIssues
        state.advance()
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        
        if state.tool_errors:
            for tool, error in state.tool_errors.items():
                state.add_issue(f"Tool {tool} failed: {error}")
                state.add_resolution_attempt(f"Using fallback data for {tool}")
                state.resolve_issue(f"Tool {tool} failed: {error}")
        
        # Phase 7: ProduceStructuredOutput
        state.advance()
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        
        # Synthesize results into TripPlan
        result = synthesize_to_tripplan(tool_results, requirements)
        
        # Add citations from tool results
        for search_result in tool_results.get("search", []):
            if isinstance(search_result, dict) and search_result.get("url"):
                state.add_citation(search_result["url"])
        
        # Store output in state
        state.set_structured_output(json.loads(result), "Travel plan generated successfully")
        
        # Phase 8: Done
        state.advance()
        logger.info(f"[PHASE] Phase: {state.phase.value} - {state.get_phase_description()}")
        
        # Add response to memory
        memory.add_conversation("assistant", result)
        
        logger.info("[OK] Request processed successfully")
        logger.info(f"[SUMMARY] State Summary: {state.get_status_summary()}")
        
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] Error in run_request: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({"error": str(e)})


def main():
    """Main entry point for command line usage."""
    try:
        logger.info("[START] Starting Travel Concierge Agent")
        
        # Validate configuration
        try:
            config = validate_all_config()
            logger.info("[OK] Configuration validated successfully")
        except Exception as e:
            logger.warning(f"[WARN] Configuration warning: {e}")
        
        # Example usage
        user_input = "I want to go to Paris from 2026-06-01 to 2026-06-08 with my BankGold card"
        
        # Run the request
        result = asyncio.run(run_request(user_input))
        
        print("\n" + "=" * 60)
        print("TRAVEL PLAN")
        print("=" * 60)
        
        # Pretty print the result
        try:
            plan_data = json.loads(result)
            print(json.dumps(plan_data, indent=2))
        except:
            print(result)
        
    except Exception as e:
        logger.error(f"[ERROR] Error in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
