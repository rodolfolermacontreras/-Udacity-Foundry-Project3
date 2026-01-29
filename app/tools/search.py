# app/tools/search.py
"""
Web Search Tool using Azure AI Agent with Bing Grounding
Provides web search capabilities for travel planning.
"""

from semantic_kernel.functions import kernel_function
import requests
import os
import json
import logging

logger = logging.getLogger(__name__)


class SearchTools:
    """Web search tools for the Travel Concierge Agent."""
    
    @kernel_function(name="web_search", description="Search the web using Bing API via Azure AI Agent")
    def web_search(self, query: str, max_results: int = 5) -> list:
        """
        Search the web using Azure AI Agent with Bing grounding.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        try:
            # Check for required environment variables
            project_endpoint = os.environ.get("PROJECT_ENDPOINT")
            agent_id = os.environ.get("AGENT_ID")
            bing_connection_id = os.environ.get("BING_CONNECTION_ID")
            
            if not all([project_endpoint, agent_id, bing_connection_id]):
                logger.warning("⚠️ Missing configuration for Azure AI Agent search")
                return [{
                    "title": "Missing configuration",
                    "url": "",
                    "snippet": "Azure AI Agent search requires PROJECT_ENDPOINT, AGENT_ID, and BING_CONNECTION_ID"
                }]
            
            logger.info(f"🔍 Searching web for: {query}")
            
            # Import Azure AI Projects client
            try:
                from azure.ai.projects import AIProjectClient
                from azure.identity import DefaultAzureCredential
            except ImportError:
                # Fallback to direct Bing API if azure-ai-projects not available
                return self._fallback_bing_search(query, max_results)
            
            # Create AI Project client
            try:
                credential = DefaultAzureCredential()
                client = AIProjectClient(
                    endpoint=project_endpoint,
                    credential=credential
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not create AI Project client: {e}")
                return self._fallback_bing_search(query, max_results)
            
            # Create a thread for the conversation
            thread = client.agents.threads.create()
            
            try:
                # Create a message with the search query
                client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=f"Search for: {query}"
                )
                
                # Run the agent with Bing grounding
                run = client.agents.runs.create_and_process(
                    thread_id=thread.id,
                    agent_id=agent_id
                )
                
                # Get the response messages
                messages = client.agents.messages.list(thread_id=thread.id)
                
                # Extract search results from the response
                results = []
                for msg in messages:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if content.get("type") == "text":
                                text = content.get("text", {}).get("value", "")
                                # Try to parse as JSON results
                                try:
                                    parsed = json.loads(text)
                                    if isinstance(parsed, list):
                                        results.extend(parsed[:max_results])
                                except json.JSONDecodeError:
                                    # If not JSON, create a single result
                                    results.append({
                                        "title": query,
                                        "url": "",
                                        "snippet": text[:500]
                                    })
                
                logger.info(f"✅ Found {len(results)} search results")
                return results[:max_results] if results else self._fallback_bing_search(query, max_results)
                
            finally:
                # Clean up the thread
                try:
                    client.agents.threads.delete(thread_id=thread.id)
                except Exception:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return [{
                "title": "Search error",
                "url": "",
                "snippet": str(e)
            }]
    
    def _fallback_bing_search(self, query: str, max_results: int = 5) -> list:
        """
        Fallback to direct Bing Search API v7.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            bing_key = os.environ.get("BING_KEY")
            
            if not bing_key:
                logger.warning("⚠️ BING_KEY not configured")
                return self._mock_search_results(query, max_results)
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": bing_key}
            params = {"q": query, "count": max_results, "mkt": "en-US"}
            
            logger.info(f"🔍 Using Bing Search API directly for: {query}")
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            web_pages = data.get("webPages", {}).get("value", [])
            
            results = []
            for page in web_pages[:max_results]:
                results.append({
                    "title": page.get("name", ""),
                    "url": page.get("url", ""),
                    "snippet": page.get("snippet", "")
                })
            
            logger.info(f"✅ Bing returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Bing search error: {e}")
            return self._mock_search_results(query, max_results)
    
    def _mock_search_results(self, query: str, max_results: int = 5) -> list:
        """
        Generate mock search results when APIs are unavailable.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of mock search results
        """
        logger.warning(f"⚠️ Using mock search results for: {query}")
        
        # Generate relevant mock results based on query keywords
        query_lower = query.lower()
        
        results = []
        
        if "restaurant" in query_lower or "food" in query_lower or "dining" in query_lower:
            results = [
                {"title": "Le Comptoir du Relais", "url": "https://example.com/le-comptoir", "snippet": "Classic French bistro in Saint-Germain, Paris. Known for excellent cuisine and atmosphere."},
                {"title": "Frenchie Restaurant", "url": "https://example.com/frenchie", "snippet": "Modern French cuisine in the 2nd arrondissement. Innovative dishes with fresh ingredients."},
                {"title": "L'Ambroisie", "url": "https://example.com/lambroisie", "snippet": "Three-Michelin-star restaurant in Place des Vosges. Exceptional French fine dining."},
            ]
        elif "hotel" in query_lower or "accommodation" in query_lower:
            results = [
                {"title": "Hotel Plaza Athénée", "url": "https://example.com/plaza-athenee", "snippet": "Luxury hotel on Avenue Montaigne with stunning Eiffel Tower views."},
                {"title": "Le Bristol Paris", "url": "https://example.com/le-bristol", "snippet": "Palace hotel near the Champs-Élysées with rooftop garden and spa."},
            ]
        elif "attraction" in query_lower or "things to do" in query_lower or "visit" in query_lower:
            results = [
                {"title": "Eiffel Tower", "url": "https://example.com/eiffel-tower", "snippet": "Iconic iron lattice tower on the Champ de Mars. Must-see Paris landmark."},
                {"title": "Louvre Museum", "url": "https://example.com/louvre", "snippet": "World's largest art museum and historic monument. Home to the Mona Lisa."},
                {"title": "Notre-Dame Cathedral", "url": "https://example.com/notre-dame", "snippet": "Medieval Catholic cathedral on the Île de la Cité."},
            ]
        else:
            results = [
                {"title": f"Top results for {query}", "url": "https://example.com/results", "snippet": f"Comprehensive guide about {query}. Find the best information and recommendations."},
            ]
        
        return results[:max_results]