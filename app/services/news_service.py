"""
News Service
Fetches interest rate related news from Google News RSS feeds.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache
import feedparser
from urllib.parse import quote
import re
from html import unescape

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching interest rate news from Google News."""
    
    GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search"
    
    # Search queries for each country
    US_QUERIES = [
        "US Treasury yield",
        "Federal Reserve interest rate",
        "10-year Treasury bond"
    ]
    
    KR_QUERIES = [
        "한국 국고채 금리",
        "한국은행 기준금리",
        "채권시장 금리",
        "미국 금리 인하",
        "연준 금리"
    ]
    
    # Cache for news (TTL: 30 minutes)
    _cache = TTLCache(maxsize=50, ttl=1800)
    
    def __init__(self):
        """Initialize the news service."""
        logger.info("News service initialized")
    
    def get_us_rate_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch US interest rate related news.
        
        Args:
            limit: Maximum number of news items to return
            
        Returns:
            List of news items
        """
        cache_key = f"us_news_{limit}"
        if cache_key in self._cache:
            logger.info("Returning cached US news")
            return self._cache[cache_key]
        
        all_news = []
        for query in self.US_QUERIES:
            news = self._fetch_google_news(query, lang="en", limit=limit)
            all_news.extend(news)
        
        # Remove duplicates and sort by date
        unique_news = self._deduplicate_news(all_news)
        sorted_news = sorted(unique_news, key=lambda x: x.get("published_at", ""), reverse=True)
        result = sorted_news[:limit]
        
        # Cache the result
        self._cache[cache_key] = result
        logger.info(f"Fetched {len(result)} US news items")
        
        return result
    
    def get_kr_rate_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch Korean interest rate related news.
        
        Args:
            limit: Maximum number of news items to return
            
        Returns:
            List of news items
        """
        cache_key = f"kr_news_{limit}"
        if cache_key in self._cache:
            logger.info("Returning cached Korean news")
            return self._cache[cache_key]
        
        all_news = []
        for query in self.KR_QUERIES:
            news = self._fetch_google_news(query, lang="ko", limit=limit)
            all_news.extend(news)
        
        # Remove duplicates and sort by date
        unique_news = self._deduplicate_news(all_news)
        sorted_news = sorted(unique_news, key=lambda x: x.get("published_at", ""), reverse=True)
        result = sorted_news[:limit]
        
        # Cache the result
        self._cache[cache_key] = result
        logger.info(f"Fetched {len(result)} Korean news items")
        
        return result
    
    def get_all_news(self, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch both US and Korean interest rate news.
        
        Args:
            limit: Maximum number of news items per country
            
        Returns:
            Dictionary with 'us' and 'kr' news lists
        """
        return {
            "us": self.get_us_rate_news(limit),
            "kr": self.get_kr_rate_news(limit)
        }
    
    def _fetch_google_news(self, query: str, lang: str = "en", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch news from Google News RSS feed.
        
        Args:
            query: Search query
            lang: Language code (en, ko)
            limit: Maximum number of items
            
        Returns:
            List of news items
        """
        try:
            # Build RSS URL
            encoded_query = quote(query)
            
            if lang == "ko":
                url = f"{self.GOOGLE_NEWS_RSS_BASE}?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
            else:
                url = f"{self.GOOGLE_NEWS_RSS_BASE}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            if feed.bozo and not feed.entries:
                logger.warning(f"Failed to parse RSS feed for query: {query}")
                return []
            
            news_items = []
            for entry in feed.entries[:limit]:
                item = self._parse_rss_entry(entry)
                if item:
                    news_items.append(item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching news for query '{query}': {e}")
            return []
    
    def _parse_rss_entry(self, entry: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS entry into news item format.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            Formatted news item or None
        """
        try:
            # Extract title
            title = unescape(entry.get("title", ""))
            
            # Extract source from title (Google News format: "Title - Source")
            source = "Unknown"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                source = parts[1] if len(parts) > 1 else "Unknown"
            
            # Extract URL
            url = entry.get("link", "")
            
            # Extract published date
            published = entry.get("published", "")
            published_at = self._parse_date(published)
            
            # Extract snippet/summary
            summary = entry.get("summary", "")
            snippet = self._clean_snippet(summary)
            
            return {
                "title": title[:200],  # Limit title length
                "source": source[:50],
                "url": url,
                "published_at": published_at,
                "snippet": snippet[:300] if snippet else ""
            }
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse date string to ISO format.
        
        Args:
            date_str: Date string from RSS
            
        Returns:
            ISO format date string
        """
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except Exception:
            return datetime.now().isoformat()
    
    def _clean_snippet(self, html_content: str) -> str:
        """
        Clean HTML content to plain text snippet.
        
        Args:
            html_content: HTML string
            
        Returns:
            Plain text string
        """
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', html_content)
        # Unescape HTML entities
        clean = unescape(clean)
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        return clean
    
    def _deduplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate news items based on URL.
        
        Args:
            news_list: List of news items
            
        Returns:
            Deduplicated list
        """
        seen_urls = set()
        unique = []
        
        for item in news_list:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(item)
        
        return unique
    
    def get_relative_time(self, iso_date: str) -> str:
        """
        Convert ISO date to relative time string (e.g., "2시간 전").
        
        Args:
            iso_date: ISO format date string
            
        Returns:
            Relative time string in Korean
        """
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            diff = now - dt
            
            if diff.days > 7:
                return dt.strftime("%Y-%m-%d")
            elif diff.days > 0:
                return f"{diff.days}일 전"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours}시간 전"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes}분 전"
            else:
                return "방금 전"
                
        except Exception:
            return ""
    
    def clear_cache(self):
        """Clear the news cache."""
        self._cache.clear()
        logger.info("News cache cleared")


# Singleton instance
_news_service_instance: Optional[NewsService] = None


def get_news_service() -> NewsService:
    """Get or create the news service singleton."""
    global _news_service_instance
    if _news_service_instance is None:
        _news_service_instance = NewsService()
    return _news_service_instance
