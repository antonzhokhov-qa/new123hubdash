"""Currency conversion service with live exchange rates."""

import json
from decimal import Decimal
from typing import Dict, Optional

import httpx
import structlog

from app.config import settings
from app.db.redis import cache

logger = structlog.get_logger()


class CurrencyService:
    """
    Service for currency conversion with live exchange rates.
    
    Features:
    - Fetches rates from exchangerate-api.com
    - Caches rates in Redis (1 hour TTL)
    - Fallback to static rates on API failure
    - Thread-safe singleton pattern
    """
    
    CACHE_KEY = "exchange_rates:usd"
    CACHE_TTL = 3600  # 1 hour
    
    # Free API (no key required for basic usage)
    API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
    
    # Fallback static rates (USD to other currencies)
    # These are inverted to get X currency -> USD
    STATIC_RATES_TO_USD: Dict[str, float] = {
        "USD": 1.0,
        "INR": 0.012,     # 1 INR = 0.012 USD (approx 83 INR = 1 USD)
        "EUR": 1.08,      # 1 EUR = 1.08 USD
        "GBP": 1.27,      # 1 GBP = 1.27 USD
        "RUB": 0.011,     # 1 RUB = 0.011 USD
        "AED": 0.27,      # 1 AED = 0.27 USD
        "BRL": 0.20,      # 1 BRL = 0.20 USD
        "CAD": 0.74,      # 1 CAD = 0.74 USD
        "AUD": 0.65,      # 1 AUD = 0.65 USD
        "JPY": 0.0067,    # 1 JPY = 0.0067 USD
        "CNY": 0.14,      # 1 CNY = 0.14 USD
        "KRW": 0.00075,   # 1 KRW = 0.00075 USD
    }
    
    _instance: Optional["CurrencyService"] = None
    _rates: Optional[Dict[str, float]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_rates(self) -> Dict[str, float]:
        """
        Get exchange rates (currency -> USD).
        
        First tries Redis cache, then API, then static fallback.
        
        Returns:
            Dict mapping currency codes to USD rates
        """
        # Try cache first
        try:
            cached = await cache.get(self.CACHE_KEY)
            if cached:
                rates = json.loads(cached)
                logger.debug("currency_rates_from_cache", currencies=len(rates))
                return rates
        except Exception as e:
            logger.warning("currency_cache_read_error", error=str(e))
        
        # Fetch from API
        rates = await self._fetch_rates_from_api()
        
        if rates:
            # Cache the rates
            try:
                await cache.set(self.CACHE_KEY, json.dumps(rates), self.CACHE_TTL)
                logger.info("currency_rates_cached", currencies=len(rates))
            except Exception as e:
                logger.warning("currency_cache_write_error", error=str(e))
            return rates
        
        # Fallback to static rates
        logger.warning("currency_using_static_rates")
        return self.STATIC_RATES_TO_USD.copy()
    
    async def _fetch_rates_from_api(self) -> Optional[Dict[str, float]]:
        """
        Fetch rates from exchange rate API.
        
        API returns rates FROM USD TO other currencies.
        We need to invert them to get FROM other currencies TO USD.
        
        Returns:
            Dict mapping currency codes to USD rates, or None on failure
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.API_URL)
                response.raise_for_status()
                
                data = response.json()
                api_rates = data.get("rates", {})
                
                # Invert rates: API gives USD -> X, we need X -> USD
                # If 1 USD = 83 INR, then 1 INR = 1/83 USD = 0.012 USD
                rates_to_usd = {}
                for currency, rate in api_rates.items():
                    if rate > 0:
                        rates_to_usd[currency] = round(1.0 / rate, 8)
                
                # USD is always 1.0
                rates_to_usd["USD"] = 1.0
                
                logger.info(
                    "currency_rates_fetched",
                    currencies=len(rates_to_usd),
                    sample_inr=rates_to_usd.get("INR"),
                    sample_eur=rates_to_usd.get("EUR"),
                )
                
                return rates_to_usd
                
        except httpx.HTTPError as e:
            logger.error("currency_api_http_error", error=str(e))
        except Exception as e:
            logger.error("currency_api_error", error=str(e))
        
        return None
    
    async def get_usd_rate(self, currency: str) -> float:
        """
        Get USD rate for a specific currency.
        
        Args:
            currency: Currency code (e.g., "INR", "EUR")
            
        Returns:
            Rate to convert 1 unit of currency to USD
        """
        currency = currency.upper()
        
        if currency == "USD":
            return 1.0
        
        rates = await self.get_rates()
        
        rate = rates.get(currency)
        if rate is None:
            logger.warning(
                "currency_unknown",
                currency=currency,
                using_default=0.0,
            )
            return 0.0
        
        return rate
    
    async def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str = "USD",
    ) -> Decimal:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code (default USD)
            
        Returns:
            Converted amount
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return amount
        
        rates = await self.get_rates()
        
        # First convert to USD
        from_rate = rates.get(from_currency, 0.0)
        if from_rate == 0.0:
            logger.warning("currency_conversion_unknown_source", currency=from_currency)
            return Decimal("0")
        
        amount_usd = amount * Decimal(str(from_rate))
        
        if to_currency == "USD":
            return amount_usd.quantize(Decimal("0.0001"))
        
        # Convert from USD to target currency
        to_rate = rates.get(to_currency, 0.0)
        if to_rate == 0.0:
            logger.warning("currency_conversion_unknown_target", currency=to_currency)
            return Decimal("0")
        
        # Invert to get USD -> target rate
        final_amount = amount_usd / Decimal(str(to_rate))
        
        return final_amount.quantize(Decimal("0.0001"))
    
    async def convert_to_usd(
        self,
        amount: Decimal,
        currency: str,
    ) -> Decimal:
        """
        Shortcut to convert amount to USD.
        
        Args:
            amount: Amount in source currency
            currency: Source currency code
            
        Returns:
            Amount in USD
        """
        return await self.convert(amount, currency, "USD")
    
    def convert_sync(
        self,
        amount: Decimal,
        currency: str,
        rate: Optional[float] = None,
    ) -> Decimal:
        """
        Synchronous conversion using provided or static rate.
        
        Useful for normalizers that need sync conversion.
        
        Args:
            amount: Amount to convert
            currency: Source currency code
            rate: Optional pre-fetched rate
            
        Returns:
            Amount in USD
        """
        currency = currency.upper()
        
        if currency == "USD":
            return amount
        
        if rate is None:
            rate = self.STATIC_RATES_TO_USD.get(currency, 0.0)
        
        if rate == 0.0:
            logger.warning("currency_sync_conversion_unknown", currency=currency)
            return Decimal("0")
        
        return (amount * Decimal(str(rate))).quantize(Decimal("0.0001"))
    
    async def refresh_rates(self) -> bool:
        """
        Force refresh rates from API.
        
        Returns:
            True if rates were successfully refreshed
        """
        rates = await self._fetch_rates_from_api()
        
        if rates:
            try:
                await cache.set(self.CACHE_KEY, json.dumps(rates), self.CACHE_TTL)
                logger.info("currency_rates_refreshed", currencies=len(rates))
                return True
            except Exception as e:
                logger.error("currency_refresh_cache_error", error=str(e))
        
        return False


# Singleton instance
currency_service = CurrencyService()
