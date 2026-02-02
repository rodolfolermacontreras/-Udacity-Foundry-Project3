# app/synthesis.py
"""
Synthesis Module for Travel Concierge Agent
Combines tool results into structured TripPlan outputs.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from app.models import TripPlan, Weather, SearchResult, CardRecommendation, CurrencyInfo

logger = logging.getLogger(__name__)


def synthesize_to_tripplan(tool_results: Dict[str, Any], requirements: Dict[str, str]) -> str:
    """
    Synthesize tool results into a comprehensive travel plan.
    
    Args:
        tool_results: Dictionary of results from various tools
        requirements: Dictionary with user requirements (destination, dates, card)
        
    Returns:
        JSON string with the complete travel plan
    """
    try:
        logger.info("🔄 Synthesizing tool results into TripPlan")
        
        # Extract destination and dates from requirements
        destination = requirements.get("destination", "Unknown")
        travel_dates = requirements.get("dates") or requirements.get("travel_dates", "Unknown")
        card_name = requirements.get("card", "BankGold")
        
        # Process weather data
        weather = extract_weather(tool_results.get("weather", {}))
        
        # Process search results
        search_results = extract_search_results(tool_results.get("search", []))
        
        # Process card recommendation
        card_recommendation = extract_card_recommendation(
            tool_results.get("card", {}),
            tool_results.get("knowledge", {}),
            card_name
        )
        
        # Process currency info
        currency_info = extract_currency_info(
            tool_results.get("fx", {}),
            card_recommendation
        )
        
        # Extract citations
        citations = extract_citations(tool_results)
        
        # Generate next steps
        next_steps = generate_next_steps(destination, card_name, weather)
        
        # Create TripPlan object
        trip_plan = TripPlan(
            destination=destination,
            travel_dates=travel_dates,
            weather=weather,
            results=search_results,
            card_recommendation=card_recommendation,
            currency_info=currency_info,
            citations=citations if citations else None,
            next_steps=next_steps
        )
        
        # Convert to dictionary and wrap in response structure
        result = {
            "plan": trip_plan.model_dump()
        }
        
        logger.info("✅ TripPlan synthesized successfully")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Error synthesizing TripPlan: {e}")
        return json.dumps({"error": str(e)})


def extract_weather(weather_data: Dict[str, Any]) -> Optional[Weather]:
    """Extract weather information from tool results."""
    try:
        if not weather_data or "error" in weather_data:
            return None
        
        daily = weather_data.get("daily", {})
        
        # Get average temperature from daily data
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        
        if temps_max and temps_min:
            avg_temp = (sum(temps_max) + sum(temps_min)) / (2 * len(temps_max))
        else:
            avg_temp = None
        
        # Interpret weather code
        weather_codes = daily.get("weathercode", [])
        conditions = interpret_weather_codes(weather_codes)
        
        # Generate recommendation
        recommendation = generate_weather_recommendation(avg_temp, conditions)
        
        return Weather(
            temperature_c=round(avg_temp, 1) if avg_temp else None,
            conditions=conditions,
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.warning(f"⚠️ Error extracting weather: {e}")
        return None


def interpret_weather_codes(codes: List[int]) -> str:
    """Interpret weather codes into human-readable conditions."""
    if not codes:
        return "Unknown"
    
    # WMO Weather interpretation codes
    code_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
    }
    
    # Get most common condition
    if not codes:
        return "Unknown"
    
    avg_code = int(sum(codes) / len(codes))
    
    # Find closest matching code
    closest_code = min(code_map.keys(), key=lambda x: abs(x - avg_code))
    return code_map.get(closest_code, "Variable conditions")


def generate_weather_recommendation(temp: Optional[float], conditions: str) -> str:
    """Generate weather-based recommendations."""
    recommendations = []
    
    if temp is not None:
        if temp < 10:
            recommendations.append("Pack warm layers and a jacket")
        elif temp < 20:
            recommendations.append("Bring light layers for mild weather")
        elif temp < 30:
            recommendations.append("Great weather for outdoor activities")
        else:
            recommendations.append("Stay hydrated and seek shade during midday")
    
    conditions_lower = conditions.lower()
    if "rain" in conditions_lower or "drizzle" in conditions_lower:
        recommendations.append("Pack an umbrella or rain jacket")
    elif "snow" in conditions_lower:
        recommendations.append("Prepare for winter conditions")
    elif "clear" in conditions_lower or "sunny" in conditions_lower:
        recommendations.append("Don't forget sunscreen and sunglasses")
    
    return "; ".join(recommendations) if recommendations else "Check local forecast before departure"


def extract_search_results(search_data: List[Dict[str, Any]]) -> Optional[List[SearchResult]]:
    """Extract search results from tool output."""
    try:
        if not search_data:
            return None
        
        results = []
        for item in search_data[:5]:  # Limit to 5 results
            if "error" in item:
                continue
            
            results.append(SearchResult(
                title=item.get("title", ""),
                snippet=item.get("snippet", item.get("description", "")),
                url=item.get("url", ""),
                price_range=item.get("price_range"),
                rating=item.get("rating"),
                category=item.get("category", "general")
            ))
        
        return results if results else None
        
    except Exception as e:
        logger.warning(f"⚠️ Error extracting search results: {e}")
        return None


def extract_card_recommendation(
    card_data: Dict[str, Any],
    knowledge_data: Dict[str, Any],
    card_name: str
) -> CardRecommendation:
    """Extract card recommendation from tool results."""
    try:
        # Try to get from card tool result
        if card_data and "best" in card_data:
            best = card_data["best"]
            return CardRecommendation(
                card=best.get("card", card_name),
                benefit=best.get("benefit", best.get("perk", "Standard rewards")),
                fx_fee=best.get("fx_fee", "None"),
                source=card_data.get("details", {}).get("source", "card_recommendation_tool")
            )
        
        # Try to get from knowledge tool result
        if knowledge_data and "card" in knowledge_data:
            return CardRecommendation(
                card=knowledge_data.get("card", card_name),
                benefit=knowledge_data.get("benefit", "Check card benefits"),
                fx_fee=knowledge_data.get("fx_fee", "None"),
                source=knowledge_data.get("source", "knowledge_base")
            )
        
        # Default recommendation
        return CardRecommendation(
            card=card_name,
            benefit="Standard rewards on purchases",
            fx_fee="No foreign transaction fees",
            source="default"
        )
        
    except Exception as e:
        logger.warning(f"⚠️ Error extracting card recommendation: {e}")
        return CardRecommendation(
            card=card_name,
            benefit="Standard rewards",
            fx_fee="None",
            source="error_fallback"
        )


def extract_currency_info(fx_data: Dict[str, Any], card_recommendation: CardRecommendation) -> CurrencyInfo:
    """Extract currency information from FX tool results."""
    try:
        sample_meal_usd = 100.0
        
        if fx_data and "rates" in fx_data:
            rates = fx_data["rates"]
            target_currency = list(rates.keys())[0] if rates else "EUR"
            # Frankfurter API returns converted amount for the input amount
            # So for 100 USD, rates['EUR'] = 84.46 means the rate is 0.8446
            converted_amount = rates.get(target_currency, 85.0)
            input_amount = fx_data.get("amount", 100.0)
            rate = converted_amount / input_amount if input_amount > 0 else 0.85
            sample_meal_foreign = round(sample_meal_usd * rate, 2)
            
            # Calculate points based on card (assume 4x for dining)
            points_multiplier = 4 if "dining" in card_recommendation.benefit.lower() else 1
            points_earned = int(sample_meal_usd * points_multiplier)
            
            return CurrencyInfo(
                usd_to_eur=round(rate, 4) if target_currency == "EUR" else None,
                sample_meal_usd=sample_meal_usd,
                sample_meal_eur=sample_meal_foreign if target_currency == "EUR" else None,
                points_earned=points_earned
            )
        
        # Default currency info
        return CurrencyInfo(
            usd_to_eur=0.85,
            sample_meal_usd=sample_meal_usd,
            sample_meal_eur=85.0,
            points_earned=400
        )
        
    except Exception as e:
        logger.warning(f"⚠️ Error extracting currency info: {e}")
        return CurrencyInfo(
            sample_meal_usd=100.0,
            points_earned=100
        )


def extract_citations(tool_results: Dict[str, Any]) -> List[str]:
    """Extract all citations from tool results."""
    citations = set()
    
    try:
        # Extract from search results
        search_data = tool_results.get("search", [])
        for item in search_data:
            if isinstance(item, dict) and "url" in item and item["url"]:
                citations.add(item["url"])
        
        # Extract from knowledge results
        knowledge_data = tool_results.get("knowledge", {})
        if isinstance(knowledge_data, dict):
            source = knowledge_data.get("source")
            if source:
                citations.add(source)
        
        # Extract from card recommendation
        card_data = tool_results.get("card", {})
        if isinstance(card_data, dict):
            details = card_data.get("details", {})
            source = details.get("source")
            if source:
                citations.add(source)
        
    except Exception as e:
        logger.warning(f"⚠️ Error extracting citations: {e}")
    
    return list(citations)


def generate_next_steps(destination: str, card_name: str, weather: Optional[Weather]) -> List[str]:
    """Generate recommended next steps for the traveler."""
    steps = []
    
    # Basic travel preparation
    steps.append(f"Book flights and accommodation for {destination}")
    steps.append(f"Notify {card_name} of your travel dates to avoid fraud alerts")
    
    # Weather-based recommendations
    if weather and weather.temperature_c:
        if weather.temperature_c < 15:
            steps.append("Pack warm clothing for cooler temperatures")
        elif weather.temperature_c > 25:
            steps.append("Pack light, breathable clothing for warm weather")
    
    # Card-related steps
    steps.append(f"Review {card_name} travel benefits before departure")
    steps.append("Download relevant travel apps and offline maps")
    steps.append("Consider travel insurance coverage review")
    
    return steps


def format_trip_plan_display(trip_plan_json: str) -> str:
    """
    Format trip plan JSON for display in chat interface.
    
    Args:
        trip_plan_json: JSON string of the trip plan
        
    Returns:
        Formatted string for display
    """
    try:
        data = json.loads(trip_plan_json)
        plan = data.get("plan", {})
        
        lines = []
        lines.append("=" * 60)
        lines.append("🎯 TRAVEL PLAN")
        lines.append("=" * 60)
        lines.append(f"📍 Destination: {plan.get('destination', 'N/A')}")
        lines.append(f"📅 Travel Dates: {plan.get('travel_dates', 'N/A')}")
        lines.append("")
        
        # Weather section
        weather = plan.get("weather")
        if weather:
            lines.append("🌤️ WEATHER")
            lines.append("-" * 30)
            lines.append(f"Temperature: {weather.get('temperature_c', 'N/A')}°C")
            lines.append(f"Conditions: {weather.get('conditions', 'N/A')}")
            lines.append(f"Recommendation: {weather.get('recommendation', 'N/A')}")
            lines.append("")
        
        # Card recommendation
        card = plan.get("card_recommendation")
        if card:
            lines.append("💳 CARD RECOMMENDATION")
            lines.append("-" * 30)
            lines.append(f"Card: {card.get('card', 'N/A')}")
            lines.append(f"Benefit: {card.get('benefit', 'N/A')}")
            lines.append(f"FX Fee: {card.get('fx_fee', 'N/A')}")
            lines.append("")
        
        # Currency info
        currency = plan.get("currency_info")
        if currency:
            lines.append("💰 CURRENCY INFO")
            lines.append("-" * 30)
            lines.append(f"Sample Meal (USD): ${currency.get('sample_meal_usd', 'N/A')}")
            if currency.get("sample_meal_eur"):
                lines.append(f"Sample Meal (EUR): €{currency['sample_meal_eur']}")
            lines.append(f"Points Earned: {currency.get('points_earned', 'N/A')}")
            lines.append("")
        
        # Next steps
        next_steps = plan.get("next_steps", [])
        if next_steps:
            lines.append("📋 NEXT STEPS")
            lines.append("-" * 30)
            for i, step in enumerate(next_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"Error formatting plan: {e}"