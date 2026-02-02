# app/tools/fx.py
"""
Currency Exchange Tool using Frankfurter API
Provides currency conversion for travel planning.
"""

from semantic_kernel.functions import kernel_function
import requests
import logging

logger = logging.getLogger(__name__)


class FxTools:
    """Currency exchange tools for the Travel Concierge Agent."""
    
    @kernel_function(name="convert_fx", description="Convert currency using Frankfurter API")
    def convert_fx(self, amount: float, base: str, target: str) -> dict:
        """
        Convert currency using the Frankfurter API.
        
        Args:
            amount: Amount to convert
            base: Source currency code (e.g., "USD")
            target: Target currency code (e.g., "EUR")
            
        Returns:
            Dictionary with conversion data including:
            - amount: Original amount
            - base: Source currency
            - date: Exchange rate date
            - rates: Dictionary with target currency and converted amount
        """
        try:
            # Frankfurter API endpoint
            url = "https://api.frankfurter.app/latest"
            
            params = {
                "amount": amount,
                "from": base.upper(),
                "to": target.upper()
            }
            
            logger.info(f"💱 Converting {amount} {base} to {target}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"[OK] Currency conversion successful: {data.get('rates', {})}")
            
            return {
                "amount": data.get("amount", amount),
                "base": data.get("base", base),
                "date": data.get("date", "Unknown"),
                "rates": data.get("rates", {target.upper(): 0})
            }
            
        except requests.exceptions.Timeout:
            logger.error("[ERROR] Currency API timeout")
            raise Exception("Currency API timeout - please try again")
        except requests.exceptions.HTTPError as e:
            logger.error(f"[ERROR] Currency API HTTP error: {e}")
            raise Exception(f"Currency API error: {e}")
        except Exception as e:
            logger.error(f"[ERROR] Currency API error: {e}")
            raise Exception(f"Failed to convert currency: {e}")
    
    @kernel_function(name="get_exchange_rate", description="Get exchange rate between two currencies")
    def get_exchange_rate(self, base: str, target: str) -> dict:
        """
        Get the exchange rate between two currencies.
        
        Args:
            base: Source currency code
            target: Target currency code
            
        Returns:
            Dictionary with exchange rate data
        """
        try:
            url = "https://api.frankfurter.app/latest"
            
            params = {
                "from": base.upper(),
                "to": target.upper()
            }
            
            logger.info(f"[STATS] Getting exchange rate: {base} → {target}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rate = data.get("rates", {}).get(target.upper(), 0)
            
            logger.info(f"[OK] Exchange rate: 1 {base} = {rate} {target}")
            
            return {
                "base": base.upper(),
                "target": target.upper(),
                "rate": rate,
                "date": data.get("date", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error getting exchange rate: {e}")
            raise
