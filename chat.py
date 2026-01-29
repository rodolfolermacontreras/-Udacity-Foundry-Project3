#!/usr/bin/env python3
"""
Travel Agent Chat Interface
Interactive chat for the AI Travel Concierge.
"""

import os
import sys
import json
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import run_request
from app.synthesis import format_trip_plan_display


def main():
    """Interactive chat interface for the travel agent"""
    print("Travel Agent Chat Interface")
    print("=" * 50)
    print("Welcome! I'm your AI travel concierge.")
    print("Tell me about your travel plans and I'll help you plan your trip!")
    print()
    print("Commands:")
    print("  help    - Show this help message")
    print("  status  - Show system status")
    print("  clear   - Clear the screen")
    print("  quit    - Exit the chat")
    print()
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("Warning: No .env file found!")
        print("   Copy env.example to .env and configure your Azure credentials.")
        print()
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye! Safe travels!")
                break
            elif user_input.lower() == 'help':
                print("\nHelp:")
                print("  Just tell me about your travel plans!")
                print("  Example: 'I want to go to Paris from June 1-8 with my BankGold card'")
                print("  I'll help you with weather, restaurants, currency, and card recommendations!")
                print()
                print("  Supported destinations: Paris, Tokyo, London, Barcelona, Rome, Berlin,")
                print("                          Sydney, Dubai, Singapore, New York")
                print()
                print("  Available cards: BankGold, BankPlatinum, BankRewards")
                continue
            elif user_input.lower() == 'status':
                print("\nSystem Status:")
                try:
                    from app.utils.config import validate_all_config
                    config = validate_all_config()
                    print("  [OK] Configuration: Valid")
                    print(f"  [OK] Azure OpenAI: {config['azure']['AZURE_OPENAI_ENDPOINT'][:30]}...")
                    print(f"  [OK] Chat Model: {config['azure']['AZURE_OPENAI_CHAT_DEPLOYMENT']}")
                    print(f"  [OK] Embedding Model: {config['azure']['AZURE_OPENAI_EMBED_DEPLOYMENT']}")
                except Exception as e:
                    print(f"  [WARN] Configuration: {e}")
                continue
            elif user_input.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            elif not user_input:
                continue
            
            # Process the request
            print("\nAgent: Let me help you plan your trip...")
            print("   (Processing your request...)")
            
            try:
                # Run the async request
                result = asyncio.run(run_request(user_input))
                
                # Parse and display the result
                try:
                    plan_data = json.loads(result)
                    
                    if "error" in plan_data:
                        print(f"\n[ERROR] {plan_data['error']}")
                    else:
                        # Validate with Pydantic
                        print("\n[OK] Response validated with Pydantic")
                        display_plan(plan_data)
                        
                except json.JSONDecodeError:
                    print("[ERROR] Could not parse the response")
                    print(f"Raw response: {result}")
                    
            except Exception as e:
                print(f"\n[ERROR] {e}")
                import traceback
                traceback.print_exc()
                
        except KeyboardInterrupt:
            print("\n\nChat stopped. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            print("Please try again or type 'help' for assistance.")


def display_plan(plan_data):
    """Display the travel plan in a formatted way"""
    if "plan" not in plan_data:
        print("[ERROR] Invalid plan format")
        return
    
    plan = plan_data["plan"]
    
    print("\n" + "="*60)
    print("TRAVEL PLAN")
    print("="*60)
    
    # Destination and dates
    print(f"Destination: {plan.get('destination', 'N/A')}")
    print(f"Travel Dates: {plan.get('travel_dates', 'N/A')}")
    print()
    
    # Weather
    weather = plan.get('weather')
    if weather:
        print("WEATHER")
        print("-" * 30)
        if weather.get('temperature_c') is not None:
            print(f"Temperature: {weather.get('temperature_c')}°C")
        print(f"Conditions: {weather.get('conditions', 'N/A')}")
        if weather.get('recommendation'):
            print(f"Recommendation: {weather['recommendation']}")
        print()
    
    # Search results (restaurants, attractions)
    results = plan.get('results')
    if results:
        print("SEARCH RESULTS")
        print("-" * 30)
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result.get('title', 'N/A')}")
            if result.get('snippet'):
                print(f"   {result['snippet'][:80]}...")
            if result.get('url'):
                print(f"   URL: {result['url']}")
            if result.get('rating'):
                print(f"   Rating: {result['rating']}/5")
            if result.get('price_range'):
                print(f"   Price: {result['price_range']}")
        print()
    
    # Card recommendation
    card = plan.get('card_recommendation')
    if card:
        print("CARD RECOMMENDATION")
        print("-" * 30)
        print(f"Card: {card.get('card', 'N/A')}")
        print(f"Benefit: {card.get('benefit', 'N/A')}")
        print(f"FX Fee: {card.get('fx_fee', 'N/A')}")
        print()
    
    # Currency info
    currency = plan.get('currency_info')
    if currency:
        print("CURRENCY INFO")
        print("-" * 30)
        if currency.get('sample_meal_usd'):
            print(f"Sample Meal (USD): ${currency['sample_meal_usd']}")
        if currency.get('sample_meal_eur'):
            print(f"Sample Meal (EUR): €{currency['sample_meal_eur']}")
        if currency.get('usd_to_eur'):
            print(f"Exchange Rate: 1 USD = {currency['usd_to_eur']} EUR")
        if currency.get('points_earned'):
            print(f"Points Earned: {currency['points_earned']}")
        print()
    
    # Next steps
    next_steps = plan.get('next_steps', [])
    if next_steps:
        print("NEXT STEPS")
        print("-" * 30)
        for i, step in enumerate(next_steps, 1):
            print(f"{i}. {step}")
        print()
    
    # Citations
    citations = plan.get('citations', [])
    if citations:
        print("SOURCES")
        print("-" * 30)
        for i, citation in enumerate(citations[:5], 1):
            print(f"{i}. {citation}")
        print()
    
    print("="*60)


if __name__ == "__main__":
    main()