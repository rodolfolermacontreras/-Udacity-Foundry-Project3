# app/tools/card.py
"""
Credit Card Recommendation Tool
Provides card recommendations based on MCC codes and travel destinations.
"""

from semantic_kernel.functions import kernel_function
import logging

logger = logging.getLogger(__name__)


# Card database with benefits and features
CARD_DATABASE = {
    "BankGold": {
        "name": "BankGold",
        "annual_fee": 0,
        "fx_fee": "None",
        "benefits": {
            "dining": "4x points on dining worldwide",
            "travel": "3x points on travel",
            "gas": "2x points on gas stations",
            "groceries": "2x points on groceries",
            "default": "1x points on all other purchases"
        },
        "perks": [
            "No foreign transaction fees",
            "Travel insurance",
            "Purchase protection",
            "Extended warranty"
        ],
        "lounge_access": False,
        "points_multiplier": {
            "5812": 4,  # Restaurants
            "5811": 4,  # Caterers
            "5814": 4,  # Fast Food
            "5541": 2,  # Gas Stations
            "5542": 2,  # Automated Fuel Dispensers
            "5411": 2,  # Grocery Stores
            "3000-3999": 3,  # Airlines
            "7011": 3,  # Hotels/Motels
        }
    },
    "BankPlatinum": {
        "name": "BankPlatinum",
        "annual_fee": 250,
        "fx_fee": "None",
        "benefits": {
            "dining": "5x points on dining worldwide",
            "travel": "5x points on travel",
            "gas": "3x points on gas stations",
            "groceries": "3x points on groceries",
            "default": "2x points on all other purchases"
        },
        "perks": [
            "No foreign transaction fees",
            "Priority Pass lounge access",
            "Global Entry/TSA PreCheck credit",
            "Travel insurance",
            "Concierge service",
            "Hotel elite status"
        ],
        "lounge_access": True,
        "points_multiplier": {
            "5812": 5,  # Restaurants
            "5811": 5,  # Caterers
            "5814": 5,  # Fast Food
            "5541": 3,  # Gas Stations
            "5542": 3,  # Automated Fuel Dispensers
            "5411": 3,  # Grocery Stores
            "3000-3999": 5,  # Airlines
            "7011": 5,  # Hotels/Motels
        }
    },
    "BankRewards": {
        "name": "BankRewards",
        "annual_fee": 95,
        "fx_fee": "None",
        "benefits": {
            "dining": "3x points on dining",
            "travel": "3x points on travel",
            "streaming": "3x points on streaming services",
            "default": "1.5x points on all other purchases"
        },
        "perks": [
            "No foreign transaction fees",
            "Cell phone protection",
            "Travel delay insurance",
            "Roadside assistance"
        ],
        "lounge_access": False,
        "points_multiplier": {
            "5812": 3,  # Restaurants
            "5811": 3,  # Caterers
            "5814": 3,  # Fast Food
            "3000-3999": 3,  # Airlines
            "7011": 3,  # Hotels/Motels
        }
    }
}

# MCC code descriptions
MCC_DESCRIPTIONS = {
    "5812": "Restaurants",
    "5811": "Caterers",
    "5814": "Fast Food Restaurants",
    "5541": "Service Stations",
    "5542": "Automated Fuel Dispensers",
    "5411": "Grocery Stores",
    "7011": "Hotels/Motels",
    "3000-3999": "Airlines",
    "4111": "Transportation",
    "5310": "Discount Stores",
    "5311": "Department Stores"
}


class CardTools:
    """Credit card recommendation tools for the Travel Concierge Agent."""
    
    @kernel_function(name="recommend_card", description="Recommend credit card based on MCC and country")
    def recommend_card(self, mcc: str, amount: float, country: str) -> dict:
        """
        Recommend the best credit card based on merchant category and country.
        
        Args:
            mcc: Merchant Category Code (e.g., "5812" for restaurants)
            amount: Transaction amount in USD
            country: Country where the purchase is made
            
        Returns:
            Dictionary with card recommendation including:
            - best: Card name, perk description, FX fee
            - explanation: Why this card is recommended
        """
        try:
            logger.info(f"[CARD] Recommending card for MCC {mcc}, ${amount} in {country}")
            
            best_card = None
            best_multiplier = 0
            best_benefit = ""
            
            # Find the best card for this MCC
            for card_name, card_data in CARD_DATABASE.items():
                multiplier = self._get_multiplier_for_mcc(card_data, mcc)
                
                if multiplier > best_multiplier:
                    best_multiplier = multiplier
                    best_card = card_data
                    best_benefit = self._get_benefit_description(card_data, mcc)
            
            # Default to BankGold if no specific match
            if not best_card:
                best_card = CARD_DATABASE["BankGold"]
                best_benefit = best_card["benefits"]["default"]
                best_multiplier = 1
            
            # Calculate points earned
            points_earned = int(amount * best_multiplier)
            
            # Get category description
            category = MCC_DESCRIPTIONS.get(mcc, "General purchase")
            
            result = {
                "best": {
                    "card": best_card["name"],
                    "benefit": best_benefit,  # Changed from "perk" to "benefit" to match tests
                    "fx_fee": best_card["fx_fee"]
                },
                "explanation": f"For {category} in {country}, {best_card['name']} earns {best_multiplier}x points. "
                              f"On ${amount:.2f}, you'll earn {points_earned} points.",
                "details": {
                    "mcc": mcc,
                    "category": category,
                    "country": country,
                    "amount": amount,
                    "points_earned": points_earned,
                    "multiplier": best_multiplier,
                    "lounge_access": best_card["lounge_access"],
                    "perks": best_card["perks"]
                }
            }
            
            logger.info(f"[OK] Recommended: {best_card['name']} with {best_multiplier}x points")
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Error recommending card: {e}")
            return {
                "best": {
                    "card": "BankGold",
                    "benefit": "Standard rewards",
                    "fx_fee": "None"
                },
                "explanation": f"Error occurred, defaulting to BankGold: {str(e)}"
            }
    
    def _get_multiplier_for_mcc(self, card_data: dict, mcc: str) -> int:
        """Get the points multiplier for a given MCC."""
        multipliers = card_data.get("points_multiplier", {})
        
        # Direct MCC match
        if mcc in multipliers:
            return multipliers[mcc]
        
        # Check airline range (3000-3999)
        try:
            mcc_int = int(mcc)
            if 3000 <= mcc_int <= 3999:
                return multipliers.get("3000-3999", 1)
        except ValueError:
            pass
        
        # Default multiplier
        return 1
    
    def _get_benefit_description(self, card_data: dict, mcc: str) -> str:
        """Get the benefit description for a given MCC."""
        benefits = card_data.get("benefits", {})
        
        # Map MCCs to benefit categories
        if mcc in ["5812", "5811", "5814"]:
            return benefits.get("dining", benefits.get("default", ""))
        elif mcc in ["5541", "5542"]:
            return benefits.get("gas", benefits.get("default", ""))
        elif mcc in ["5411"]:
            return benefits.get("groceries", benefits.get("default", ""))
        elif mcc in ["7011"] or (mcc.isdigit() and 3000 <= int(mcc) <= 3999):
            return benefits.get("travel", benefits.get("default", ""))
        
        return benefits.get("default", "Standard rewards")
    
    @kernel_function(name="get_card_perks", description="Get all perks for a specific card")
    def get_card_perks(self, card_name: str) -> dict:
        """
        Get all perks and benefits for a specific card.
        
        Args:
            card_name: Name of the card (e.g., "BankGold")
            
        Returns:
            Dictionary with card details and perks
        """
        try:
            card_data = CARD_DATABASE.get(card_name)
            
            if not card_data:
                # Try case-insensitive match
                for name, data in CARD_DATABASE.items():
                    if name.lower() == card_name.lower():
                        card_data = data
                        break
            
            if not card_data:
                return {"error": f"Card '{card_name}' not found in database"}
            
            return {
                "card": card_data["name"],
                "annual_fee": card_data["annual_fee"],
                "fx_fee": card_data["fx_fee"],
                "benefits": card_data["benefits"],
                "perks": card_data["perks"],
                "lounge_access": card_data["lounge_access"]
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error getting card perks: {e}")
            return {"error": str(e)}
