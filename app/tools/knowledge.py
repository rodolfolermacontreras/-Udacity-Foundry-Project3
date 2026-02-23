# app/tools/knowledge.py
"""
Knowledge Base Tool using RAG retrieval
Provides knowledge retrieval for card benefits and travel policies.
"""

from semantic_kernel.functions import kernel_function
from app.rag.retriever import retrieve
import logging

logger = logging.getLogger(__name__)


# Local knowledge base for fallback
LOCAL_KNOWLEDGE_BASE = {
    "BankGold": {
        "card": "BankGold",
        "dining_benefit": "4x points on dining worldwide",
        "travel_benefit": "3x points on travel purchases",
        "fx_fee": "No foreign transaction fees",
        "lounge_access": "No airport lounge access included",
        "travel_insurance": "Basic travel insurance coverage included",
        "perks": [
            "No annual fee",
            "No foreign transaction fees",
            "Purchase protection up to $500",
            "Extended warranty on purchases"
        ],
        "source": "Banking International Card Benefits Guide"
    },
    "BankPlatinum": {
        "card": "BankPlatinum",
        "dining_benefit": "5x points on dining worldwide",
        "travel_benefit": "5x points on travel purchases",
        "fx_fee": "No foreign transaction fees",
        "lounge_access": "Unlimited Priority Pass lounge access",
        "travel_insurance": "Comprehensive travel insurance with trip cancellation coverage",
        "perks": [
            "$250 annual fee",
            "Priority Pass lounge access",
            "$200 annual travel credit",
            "Global Entry/TSA PreCheck credit",
            "Hotel elite status",
            "Concierge service 24/7"
        ],
        "source": "Banking International Card Benefits Guide"
    },
    "BankRewards": {
        "card": "BankRewards",
        "dining_benefit": "3x points on dining",
        "travel_benefit": "3x points on travel",
        "fx_fee": "No foreign transaction fees",
        "lounge_access": "No lounge access",
        "travel_insurance": "Travel delay insurance included",
        "perks": [
            "$95 annual fee (waived first year)",
            "Cell phone protection",
            "Roadside assistance",
            "Streaming service credits"
        ],
        "source": "Banking International Card Benefits Guide"
    },
    "lounge_rules": {
        "priority_pass": "Priority Pass lounges allow access for cardholder plus 2 guests",
        "dress_code": "Smart casual attire recommended in most lounges",
        "hours": "Lounge access typically limited to 3 hours before departure",
        "restrictions": "Some lounges may have capacity restrictions during peak hours",
        "source": "Banking International Lounge Access Policy"
    },
    "travel_insurance": {
        "trip_cancellation": "Up to $10,000 per trip for non-refundable expenses",
        "trip_delay": "Up to $500 per delay for meals and accommodations",
        "baggage_delay": "Up to $200 for essential purchases",
        "medical_coverage": "Up to $50,000 emergency medical coverage abroad",
        "source": "Banking International Travel Insurance Summary"
    }
}


class KnowledgeTools:
    """Knowledge base tools for the Travel Concierge Agent."""
    
    @kernel_function(name="get_card_recommendation", description="Get card recommendation from knowledge base")
    def get_card_recommendation(self, mcc: str, country: str) -> dict:
        """
        Get card recommendation from knowledge base using vector search.
        
        Args:
            mcc: Merchant Category Code
            country: Destination country
            
        Returns:
            Dictionary with card recommendation and benefits
        """
        try:
            logger.info(f"[KB] Querying knowledge base for MCC {mcc} in {country}")
            
            # Construct search query
            query = f"best credit card benefits for {self._mcc_to_category(mcc)} purchases in {country}"
            
            # Try RAG retrieval first
            try:
                results = retrieve(query, k=3)
                if results and not any('error' in r for r in results):
                    logger.info(f"[OK] Retrieved {len(results)} results from knowledge base")
                    return self._format_rag_results(results, mcc, country)
            except Exception as e:
                logger.warning(f"[WARN] RAG retrieval failed, using local knowledge: {e}")
            
            # Fallback to local knowledge base
            return self._get_local_recommendation(mcc, country)
            
        except Exception as e:
            logger.error(f"[ERROR] Error getting card recommendation: {e}")
            return {
                "card": "BankGold",
                "benefit": "General rewards on all purchases",
                "source": "Default recommendation"
            }
    
    @kernel_function(name="search_knowledge", description="Search the knowledge base for specific information")
    def search_knowledge(self, query: str) -> dict:
        """
        Search the knowledge base for specific information.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with search results and sources
        """
        try:
            logger.info(f"[SEARCH] Searching knowledge base: {query}")
            
            # Try RAG retrieval first
            try:
                results = retrieve(query, k=5)
                if results and not any('error' in r for r in results):
                    return {
                        "query": query,
                        "results": results,
                        "source": "RAG knowledge base"
                    }
            except Exception as e:
                logger.warning(f"[WARN] RAG search failed: {e}")
            
            # Fallback to local knowledge search
            return self._search_local_knowledge(query)
            
        except Exception as e:
            logger.error(f"[ERROR] Knowledge search error: {e}")
            return {"error": str(e)}
    
    @kernel_function(name="get_lounge_rules", description="Get airport lounge access rules")
    def get_lounge_rules(self, card_name: str) -> dict:
        """
        Get airport lounge access rules for a specific card.
        
        Args:
            card_name: Name of the credit card
            
        Returns:
            Dictionary with lounge access information
        """
        try:
            logger.info(f"[LOUNGE] Getting lounge rules for {card_name}")
            
            card_info = LOCAL_KNOWLEDGE_BASE.get(card_name)
            lounge_rules = LOCAL_KNOWLEDGE_BASE.get("lounge_rules", {})
            
            if card_info:
                return {
                    "card": card_name,
                    "lounge_access": card_info.get("lounge_access", "No lounge access"),
                    "rules": lounge_rules,
                    "source": card_info.get("source", "Banking International")
                }
            
            return {
                "card": card_name,
                "lounge_access": "Card not found in knowledge base",
                "rules": lounge_rules,
                "source": "Banking International Lounge Policy"
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error getting lounge rules: {e}")
            return {"error": str(e)}
    
    @kernel_function(name="get_travel_insurance", description="Get travel insurance details for a card")
    def get_travel_insurance(self, card_name: str) -> dict:
        """
        Get travel insurance details for a specific card.
        
        Args:
            card_name: Name of the credit card
            
        Returns:
            Dictionary with travel insurance information
        """
        try:
            logger.info(f"[INSURANCE] Getting travel insurance for {card_name}")
            
            card_info = LOCAL_KNOWLEDGE_BASE.get(card_name)
            insurance_info = LOCAL_KNOWLEDGE_BASE.get("travel_insurance", {})
            
            if card_info:
                return {
                    "card": card_name,
                    "coverage_summary": card_info.get("travel_insurance", "Basic coverage"),
                    "details": insurance_info,
                    "source": card_info.get("source", "Banking International")
                }
            
            return {
                "card": card_name,
                "coverage_summary": "Standard travel protection",
                "details": insurance_info,
                "source": "Banking International Travel Insurance Policy"
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error getting travel insurance: {e}")
            return {"error": str(e)}
    
    def _mcc_to_category(self, mcc: str) -> str:
        """Convert MCC code to category description."""
        mcc_map = {
            "5812": "restaurant dining",
            "5811": "catering",
            "5814": "fast food",
            "5541": "gas station",
            "5542": "fuel",
            "5411": "grocery",
            "7011": "hotel",
            "4111": "transportation"
        }
        
        # Check for airline MCCs (3000-3999)
        try:
            mcc_int = int(mcc)
            if 3000 <= mcc_int <= 3999:
                return "airline"
        except ValueError:
            pass
        
        return mcc_map.get(mcc, "general")
    
    def _format_rag_results(self, results: list, mcc: str, country: str) -> dict:
        """Format RAG retrieval results into card recommendation."""
        # Extract best matching card from results
        best_result = results[0] if results else {}
        content = best_result.get("content", "")
        
        # Try to extract card name from content
        card_name = "BankGold"  # Default
        for card in ["BankPlatinum", "BankGold", "BankRewards"]:
            if card.lower() in content.lower():
                card_name = card
                break
        
        return {
            "card": card_name,
            "benefit": content[:200] if content else "Check knowledge base for details",
            "source": best_result.get("metadata", {}).get("source", "RAG knowledge base"),
            "relevance_score": best_result.get("metadata", {}).get("relevance_score", 0.0)
        }
    
    def _get_local_recommendation(self, mcc: str, country: str) -> dict:
        """Get recommendation from local knowledge base."""
        category = self._mcc_to_category(mcc)
        
        # Determine best card based on category
        if category in ["restaurant dining", "catering", "fast food"]:
            card = LOCAL_KNOWLEDGE_BASE["BankPlatinum"]
            benefit = card["dining_benefit"]
        elif category in ["airline", "hotel", "transportation"]:
            card = LOCAL_KNOWLEDGE_BASE["BankPlatinum"]
            benefit = card["travel_benefit"]
        else:
            card = LOCAL_KNOWLEDGE_BASE["BankGold"]
            benefit = "Standard rewards on all purchases"
        
        return {
            "card": card["card"],
            "benefit": benefit,
            "fx_fee": card["fx_fee"],
            "source": card["source"]
        }
    
    def _search_local_knowledge(self, query: str) -> dict:
        """Search local knowledge base for matching content."""
        query_lower = query.lower()
        matches = []
        
        for key, value in LOCAL_KNOWLEDGE_BASE.items():
            if isinstance(value, dict):
                # Search in all string values
                for k, v in value.items():
                    if isinstance(v, str) and query_lower in v.lower():
                        matches.append({
                            "topic": key,
                            "field": k,
                            "content": v,
                            "source": value.get("source", "Banking International")
                        })
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str) and query_lower in item.lower():
                                matches.append({
                                    "topic": key,
                                    "field": k,
                                    "content": item,
                                    "source": value.get("source", "Banking International")
                                })
        
        return {
            "query": query,
            "results": matches[:5],
            "source": "Local knowledge base"
        }
