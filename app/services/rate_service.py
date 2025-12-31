"""
Interest Rate Data Service
Fetches US and Korean 10-Year Treasury yields from FRED and ECOS APIs.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from functools import lru_cache
from cachetools import TTLCache
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateDataService:
    """Service for fetching interest rate data from FRED and ECOS APIs."""
    
    # FRED API Configuration
    FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    FRED_SERIES_ID = "DGS10"  # 10-Year Treasury Constant Maturity Rate
    
    # ECOS API Configuration
    ECOS_BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"
    ECOS_TABLE_CODE = "817Y002"  # 채권/금리 (국고채 10년)
    ECOS_ITEM_CODE = "010210000"  # 국고채(10년)
    
    # Cache for rate data (TTL: 1 hour)
    _cache = TTLCache(maxsize=100, ttl=3600)
    
    def __init__(self, fred_api_key: Optional[str] = None, ecos_api_key: Optional[str] = None):
        """Initialize the service with API keys."""
        self.fred_api_key = fred_api_key or os.getenv('FRED_API_KEY')
        self.ecos_api_key = ecos_api_key or os.getenv('ECOS_API_KEY')
        
        if not self.fred_api_key:
            logger.warning("FRED API key not provided. US rate data will not be available.")
        if not self.ecos_api_key:
            logger.warning("ECOS API key not provided. Korean rate data will not be available.")
    
    def get_us_treasury_10y(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch US 10-Year Treasury yield from FRED API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with columns: date, us_rate
        """
        cache_key = f"us_{start_date}_{end_date}"
        if cache_key in self._cache:
            logger.info("Returning cached US rate data")
            return self._cache[cache_key]
        
        if not self.fred_api_key:
            logger.error("FRED API key is required")
            return self._get_mock_us_data(start_date, end_date)
        
        try:
            params = {
                "series_id": self.FRED_SERIES_ID,
                "api_key": self.fred_api_key,
                "file_type": "json",
                "observation_start": start_date,
                "observation_end": end_date,
                "sort_order": "asc"
            }
            
            response = self._make_request(self.FRED_BASE_URL, params)
            
            if response and "observations" in response:
                observations = response["observations"]
                df = pd.DataFrame(observations)
                
                # Clean and transform data
                df = df[["date", "value"]].copy()
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                df = df.dropna(subset=["value"])
                df.columns = ["date", "us_rate"]
                df["date"] = pd.to_datetime(df["date"])
                
                # Cache the result
                self._cache[cache_key] = df
                logger.info(f"Fetched {len(df)} US rate observations")
                return df
            else:
                logger.warning("No observations found in FRED response")
                return self._get_mock_us_data(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error fetching US rate data: {e}")
            return self._get_mock_us_data(start_date, end_date)
    
    def get_kr_treasury_10y(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch Korean 10-Year Treasury yield from ECOS API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with columns: date, kr_rate
        """
        cache_key = f"kr_{start_date}_{end_date}"
        if cache_key in self._cache:
            logger.info("Returning cached Korean rate data")
            return self._cache[cache_key]
        
        if not self.ecos_api_key:
            logger.error("ECOS API key is required")
            return self._get_mock_kr_data(start_date, end_date)
        
        try:
            # Convert dates to ECOS format (YYYYMMDD)
            start_ecos = start_date.replace("-", "")
            end_ecos = end_date.replace("-", "")
            
            # Build ECOS API URL
            url = (
                f"{self.ECOS_BASE_URL}/{self.ecos_api_key}/json/kr/1/1000/"
                f"{self.ECOS_TABLE_CODE}/D/{start_ecos}/{end_ecos}/{self.ECOS_ITEM_CODE}"
            )
            
            response = self._make_request(url)
            
            if response and "StatisticSearch" in response:
                rows = response["StatisticSearch"].get("row", [])
                
                if rows:
                    df = pd.DataFrame(rows)
                    df = df[["TIME", "DATA_VALUE"]].copy()
                    df.columns = ["date", "kr_rate"]
                    
                    # Parse date and rate
                    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
                    df["kr_rate"] = pd.to_numeric(df["kr_rate"], errors="coerce")
                    df = df.dropna(subset=["kr_rate"])
                    df = df.sort_values("date").reset_index(drop=True)
                    
                    # Cache the result
                    self._cache[cache_key] = df
                    logger.info(f"Fetched {len(df)} Korean rate observations")
                    return df
                else:
                    logger.warning("No rows found in ECOS response")
                    return self._get_mock_kr_data(start_date, end_date)
            else:
                logger.warning("Invalid ECOS response format")
                return self._get_mock_kr_data(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error fetching Korean rate data: {e}")
            return self._get_mock_kr_data(start_date, end_date)
    
    def get_combined_rates(self, days: int = 90, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get combined US and Korean rate data with spread calculation.

        Args:
            days: Number of days of data to fetch (default: 90) - ignored if start_date/end_date provided
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format

        Returns:
            DataFrame with columns: date, us_rate, kr_rate, spread
        """
        # Use explicit date range if provided, otherwise calculate from days
        if start_date and end_date:
            start_str = start_date
            end_str = end_date
            cache_key = f"combined_{start_date}_{end_date}"
        else:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days + 10)  # Extra days for holidays
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = end_dt.strftime("%Y-%m-%d")
            cache_key = f"combined_{days}"

        if cache_key in self._cache:
            logger.info("Returning cached combined rate data")
            return self._cache[cache_key]
        
        # Fetch both rates
        us_df = self.get_us_treasury_10y(start_str, end_str)
        kr_df = self.get_kr_treasury_10y(start_str, end_str)
        
        # Merge on date
        if us_df.empty and kr_df.empty:
            logger.warning("Both rate datasets are empty")
            return pd.DataFrame(columns=["date", "us_rate", "kr_rate", "spread"])
        
        # Outer merge to keep all dates
        combined = pd.merge(us_df, kr_df, on="date", how="outer")
        combined = combined.sort_values("date").reset_index(drop=True)
        
        # Forward fill missing values
        combined["us_rate"] = combined["us_rate"].ffill()
        combined["kr_rate"] = combined["kr_rate"].ffill()
        
        # Drop any remaining NaN rows
        combined = combined.dropna()
        
        # Calculate spread (Korea - US) in basis points
        combined["spread"] = (combined["kr_rate"] - combined["us_rate"]) * 100
        
        # Keep only the most recent 'days' entries
        combined = combined.tail(days).reset_index(drop=True)
        
        # Cache the result
        self._cache[cache_key] = combined
        logger.info(f"Combined rate data: {len(combined)} observations")
        
        return combined
    
    def get_latest_rates(self) -> Dict[str, Any]:
        """
        Get the most recent rate data.
        
        Returns:
            Dictionary with latest rates and metadata
        """
        combined = self.get_combined_rates(days=30)
        
        if combined.empty:
            return {
                "us_rate": None,
                "kr_rate": None,
                "spread": None,
                "date": None,
                "error": "No data available"
            }
        
        latest = combined.iloc[-1]
        
        return {
            "us_rate": round(float(latest["us_rate"]), 3),
            "kr_rate": round(float(latest["kr_rate"]), 3),
            "spread": round(float(latest["spread"]), 1),
            "date": latest["date"].strftime("%Y-%m-%d"),
            "error": None
        }
    
    def _make_request(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: Request URL
            params: Query parameters (optional)
            max_retries: Maximum number of retries
            
        Returns:
            JSON response or None
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(wait_time)
        
        return None
    
    def _get_mock_us_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate mock US rate data for development/testing."""
        import numpy as np
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
        base_rate = 4.25
        np.random.seed(42)
        rates = base_rate + np.cumsum(np.random.randn(len(dates)) * 0.02)
        
        return pd.DataFrame({
            "date": dates,
            "us_rate": rates.clip(3.5, 5.0)  # Realistic range
        })
    
    def _get_mock_kr_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate mock Korean rate data for development/testing."""
        import numpy as np
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
        base_rate = 3.45
        np.random.seed(43)
        rates = base_rate + np.cumsum(np.random.randn(len(dates)) * 0.015)
        
        return pd.DataFrame({
            "date": dates,
            "kr_rate": rates.clip(2.8, 4.2)  # Realistic range
        })
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Rate data cache cleared")


# Singleton instance
_rate_service_instance: Optional[RateDataService] = None


def get_rate_service() -> RateDataService:
    """Get or create the rate service singleton."""
    global _rate_service_instance
    if _rate_service_instance is None:
        _rate_service_instance = RateDataService()
    return _rate_service_instance
