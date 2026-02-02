# app/knowledge_base.py
from typing import Dict, Any, Optional, List

# Local knowledge base for card benefits
CARD_BENEFITS = {
    "BankGold": {
        "card": "BankGold",
        "dining": "4x points on dining worldwide",
        "travel": "3x points on travel purchases",
        "fx_fee": "No foreign transaction fees",
        "lounge": "Complimentary lounge access at select locations",
        "insurance": "Basic travel insurance included",
        "annual_fee": "$150"
    },
    "BankPlatinum": {
        "card": "BankPlatinum",
        "dining": "5x points on dining worldwide",
        "travel": "5x points on travel and hotels",
        "fx_fee": "No foreign transaction fees",
        "lounge": "Unlimited Priority Pass lounge access",
        "insurance": "Comprehensive travel insurance up to $500,000",
        "annual_fee": "$450"
    },
    "BankRewards": {
        "card": "BankRewards",
        "dining": "3x points on dining",
        "travel": "2x points on all purchases",
        "fx_fee": "No foreign transaction fees",
        "lounge": "No lounge access",
        "insurance": "Basic travel delay insurance",
        "annual_fee": "$95"
    }
}


def search_card_benefits(card_name: str, benefit_type: str = None) -> List[Dict[str, Any]]:
    """
    Search for card benefits in the knowledge base.
    
    Args:
        card_name: Name of the card (e.g., "BankGold")
        benefit_type: Optional benefit type to filter (e.g., "dining")
        
    Returns:
        List of matching benefits
    """
    results = []
    
    # Search for matching cards
    for name, benefits in CARD_BENEFITS.items():
        if card_name.lower() in name.lower():
            if benefit_type:
                # Filter by benefit type
                for key, value in benefits.items():
                    if benefit_type.lower() in key.lower():
                        results.append({
                            "card": name,
                            "benefit_type": key,
                            "benefit": value,
                            "source": "Banking International Knowledge Base"
                        })
            else:
                # Return all benefits for the card
                results.append({
                    "card": name,
                    "benefits": benefits,
                    "source": "Banking International Knowledge Base"
                })
    
    return results


def get_card_recommendation(mcc: str, country: str) -> Dict[str, Any]:
    """
    Get card recommendation from knowledge base based on MCC and country.
    
    Args:
        mcc: Merchant Category Code
        country: Destination country
        
    Returns:
        Card recommendation with benefits
    """
    # MCC-based recommendations
    # 5812 = Restaurants, 7011 = Hotels, 3000-3999 = Airlines
    if mcc == "5812":  # Dining
        return {
            "card": "BankPlatinum",
            "benefit": "5x points on dining worldwide",
            "fx_fee": "None",
            "source": "Banking International MCC Benefits Guide"
        }
    elif mcc == "7011":  # Hotels
        return {
            "card": "BankPlatinum",
            "benefit": "5x points on hotels with lounge access",
            "fx_fee": "None",
            "source": "Banking International MCC Benefits Guide"
        }
    else:
        return {
            "card": "BankGold",
            "benefit": "4x points on dining, 3x on travel",
            "fx_fee": "None",
            "source": "Banking International Card Benefits Guide"
        }
