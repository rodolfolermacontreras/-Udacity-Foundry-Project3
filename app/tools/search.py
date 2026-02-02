# app/tools/search.py
"""
Web Search Tool using Azure AI Foundry Agent with Bing Grounding
Provides web search capabilities for travel planning.
"""

from semantic_kernel.functions import kernel_function
import os
import logging

logger = logging.getLogger(__name__)


class SearchTools:
    """Web search tools for the Travel Concierge Agent."""
    
    @kernel_function(name="web_search", description="Search the web for travel information")
    def web_search(self, query: str, max_results: int = 5) -> list:
        """
        Search the web using Azure AI Foundry Agent with Bing grounding.
        Falls back to mock results if agent is unavailable.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        # Try Azure AI Foundry Agent first
        agent_results = self._search_with_agent(query, max_results)
        if agent_results:
            return agent_results
        
        # Fallback to mock results
        return self._mock_search_results(query, max_results)
    
    def _search_with_agent(self, query: str, max_results: int = 5) -> list:
        """
        Search using Azure AI Foundry Agent with Bing Grounding.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of search results or None if failed
        """
        try:
            # Get configuration
            project_endpoint = os.environ.get("PROJECT_ENDPOINT")
            api_key = os.environ.get("AZURE_OPENAI_KEY")
            agent_id = os.environ.get("AGENT_ID")
            
            if not all([project_endpoint, api_key, agent_id]):
                logger.info("Agent configuration incomplete - skipping agent search")
                return None
            
            logger.info(f"Searching with AI Foundry Agent for: {query}")
            
            # Use azure-ai-projects SDK
            try:
                from azure.ai.projects import AIProjectClient
                from azure.identity import DefaultAzureCredential
                from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions
                
                # Create client with DefaultAzureCredential (uses Azure CLI login)
                client = AIProjectClient(
                    endpoint=project_endpoint,
                    credential=DefaultAzureCredential()
                )
                
                # Create thread options with the initial message
                thread_options = AgentThreadCreationOptions(
                    messages=[
                        ThreadMessageOptions(
                            role="user",
                            content=f"Search the web and provide information about: {query}"
                        )
                    ]
                )
                
                # Create a thread and run the agent
                run = client.agents.create_thread_and_process_run(
                    agent_id=agent_id,
                    thread=thread_options
                )
                
                if run.status == "completed":
                    # Get messages from the thread (returns ItemPaged)
                    messages = client.agents.messages.list(thread_id=run.thread_id)
                    
                    for msg in messages:
                        if msg.role == "assistant":
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    text = content.text.value if hasattr(content.text, 'value') else str(content.text)
                                    logger.info(f"Agent returned response for: {query}")
                                    return [{
                                        "title": f"Web search: {query}",
                                        "url": "https://bing.com",
                                        "snippet": text[:1500]
                                    }]
                
                logger.warning(f"Agent run status: {run.status}")
                return None
                
            except ImportError:
                logger.warning("azure-ai-projects not installed - trying OpenAI Assistants API")
                return self._search_with_openai_assistants(query, max_results)
                
            except Exception as e:
                logger.warning(f"AI Foundry Agent search failed: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None
    
    def _search_with_openai_assistants(self, query: str, max_results: int = 5) -> list:
        """
        Fallback: Search using OpenAI Assistants API directly.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of search results or None if failed
        """
        try:
            from openai import AzureOpenAI
            
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            api_key = os.environ.get("AZURE_OPENAI_KEY")
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
            agent_id = os.environ.get("AGENT_ID")
            
            if not all([endpoint, api_key, agent_id]):
                return None
            
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            
            # Create thread and run
            thread = client.beta.threads.create()
            
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Search the web for: {query}"
            )
            
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=agent_id
            )
            
            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if content.type == "text":
                                logger.info(f"OpenAI Assistant returned response for: {query}")
                                return [{
                                    "title": f"Web search: {query}",
                                    "url": "https://bing.com",
                                    "snippet": content.text.value[:1500]
                                }]
            
            return None
            
        except Exception as e:
            logger.warning(f"OpenAI Assistants API failed: {e}")
            return None
    
    def _mock_search_results(self, query: str, max_results: int = 5) -> list:
        """
        Generate mock search results when APIs are unavailable.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of mock search results
        """
        logger.info(f"Using mock search results for: {query}")
        
        query_lower = query.lower()
        results = []
        
        # Destination-specific results
        if "paris" in query_lower:
            if "restaurant" in query_lower or "food" in query_lower or "dining" in query_lower:
                results = [
                    {"title": "Le Comptoir du Relais", "url": "https://lecomptoirparis.com", "snippet": "Classic French bistro in Saint-Germain-des-Pres, Paris. Known for excellent prix-fixe dinners and traditional cuisine. Reservations required."},
                    {"title": "Frenchie Restaurant", "url": "https://frenchie-restaurant.com", "snippet": "Modern French cuisine in the 2nd arrondissement. Chef Gregory Marchand creates innovative dishes with fresh seasonal ingredients."},
                    {"title": "L'Ambroisie", "url": "https://ambroisie-paris.com", "snippet": "Three-Michelin-star restaurant in Place des Vosges. Exceptional French fine dining in an elegant 17th-century setting."},
                ]
            elif "hotel" in query_lower or "stay" in query_lower or "accommodation" in query_lower:
                results = [
                    {"title": "Hotel Plaza Athenee", "url": "https://plaza-athenee-paris.com", "snippet": "Luxury 5-star hotel on Avenue Montaigne with stunning Eiffel Tower views. Features Alain Ducasse restaurant and world-class spa."},
                    {"title": "Le Bristol Paris", "url": "https://lebristolparis.com", "snippet": "Palace hotel near the Champs-Elysees with rooftop garden, Epicure restaurant (3 Michelin stars), and elegant rooms."},
                    {"title": "Hotel Le Marais", "url": "https://hotel-lemarais.com", "snippet": "Boutique hotel in the historic Marais district. Walking distance to Notre-Dame, Centre Pompidou, and charming cafes."},
                ]
            else:
                results = [
                    {"title": "Eiffel Tower - Official Site", "url": "https://toureiffel.paris", "snippet": "Iconic iron lattice tower on the Champ de Mars. Visit the summit for panoramic views of Paris. Open daily, advance tickets recommended."},
                    {"title": "Louvre Museum", "url": "https://louvre.fr", "snippet": "World's largest art museum housing the Mona Lisa, Venus de Milo, and over 35,000 works. Plan at least half a day for your visit."},
                    {"title": "Paris Travel Guide 2026", "url": "https://parisinfo.com", "snippet": "Complete guide to visiting Paris: top attractions, neighborhoods, metro tips, best times to visit, and local recommendations."},
                ]
        elif "tokyo" in query_lower:
            results = [
                {"title": "Tokyo Travel Guide", "url": "https://gotokyo.org", "snippet": "Official Tokyo tourism guide. Explore Shibuya, Shinjuku, traditional temples, and world-class cuisine in Japan's capital."},
                {"title": "Best Things to Do in Tokyo", "url": "https://timeout.com/tokyo", "snippet": "Top attractions include Senso-ji Temple, Meiji Shrine, Tsukiji Outer Market, and the vibrant nightlife of Roppongi."},
            ]
        elif "rome" in query_lower:
            results = [
                {"title": "Rome Travel Guide", "url": "https://turismoroma.it", "snippet": "Discover ancient history at the Colosseum, Roman Forum, and Vatican City. Experience Italian cuisine and la dolce vita."},
                {"title": "Vatican Museums", "url": "https://museivaticani.va", "snippet": "Home to the Sistine Chapel and extensive art collections. Book tickets in advance to avoid long queues."},
            ]
        # Generic travel-related results
        elif "restaurant" in query_lower or "food" in query_lower or "dining" in query_lower:
            results = [
                {"title": "Top Restaurant Recommendations", "url": "https://tripadvisor.com", "snippet": "Find highly-rated restaurants based on traveler reviews. Filter by cuisine type, price range, and location."},
                {"title": "Local Dining Guide", "url": "https://eater.com", "snippet": "Expert recommendations for the best local restaurants, from fine dining to hidden gems and street food."},
            ]
        elif "hotel" in query_lower or "stay" in query_lower or "accommodation" in query_lower:
            results = [
                {"title": "Hotel Booking Guide", "url": "https://booking.com", "snippet": "Compare hotel prices and amenities. Read verified guest reviews and book with free cancellation options."},
                {"title": "Best Areas to Stay", "url": "https://tripadvisor.com", "snippet": "Neighborhood guides to help you choose the best location for your trip based on attractions and transportation."},
            ]
        elif "attraction" in query_lower or "things to do" in query_lower or "visit" in query_lower:
            results = [
                {"title": "Top Attractions & Activities", "url": "https://viator.com", "snippet": "Book tours, activities, and experiences. Skip-the-line tickets and guided tours available."},
                {"title": "Travel Itinerary Ideas", "url": "https://lonelyplanet.com", "snippet": "Expert travel guides with suggested itineraries, must-see attractions, and off-the-beaten-path recommendations."},
            ]
        else:
            # Default generic results
            results = [
                {"title": f"Travel Guide: {query}", "url": "https://lonelyplanet.com", "snippet": f"Comprehensive travel information about {query}. Find attractions, restaurants, hotels, and local tips."},
                {"title": f"{query} - Tourism Information", "url": "https://tripadvisor.com", "snippet": f"Plan your trip with reviews, photos, and travel advice from millions of travelers who visited {query}."},
            ]
        
        return results[:max_results]

