"""
AI Analysis Service using Groq API with Qwen3 32B
Generates market analysis for interest rate trends.
"""

import os
import logging
import requests
from typing import Optional
from datetime import datetime
from cachetools import TTLCache
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAnalysisService:
    """Service for generating AI-powered interest rate analysis using Groq + Qwen."""

    # Groq API endpoint
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    # Qwen3 32B model on Groq
    MODEL_NAME = "qwen/qwen3-32b"

    # Cache for analysis (TTL: 6 hours)
    _cache = TTLCache(maxsize=10, ttl=21600)

    # Analysis prompt template
    ANALYSIS_PROMPT = """당신은 채권 시장 전문 애널리스트입니다. 아래의 미국과 한국 10년물 국고채 금리 데이터와 한국 최신 뉴스를 종합하여 시장 동향을 분석해 주세요.

## 금리 데이터
### 미국 10년물 국고채 금리 (최근 30일)
{us_data}

### 한국 10년물 국고채 금리 (최근 30일)
{kr_data}

### 현재 스프레드 (한국 - 미국)
{spread}bp

## 한국 금리 관련 최신 뉴스
{kr_news}

## 요구사항
- 정확히 3문장으로 요약하세요.
- 첫 번째 문장: 미국과 한국 금리 추세를 분석하세요.
- 두 번째 문장: 한국 뉴스에서 언급된 주요 이슈(한은 정책, 경제 지표, 시장 동향 등)를 반영하세요.
- 세 번째 문장: 향후 단기 전망 또는 투자자가 주의해야 할 포인트를 제시하세요.
- 전문적이면서도 간결한 애널리스트 톤으로 작성하세요.
- 구체적인 수치를 포함하세요.

/no_think

분석 결과:"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI service with API key."""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')

        if self.api_key:
            logger.info("Groq AI analysis service initialized with Qwen3 32B")
        else:
            logger.warning("Groq API key not provided")

    def generate_rate_analysis(
        self,
        us_rates: pd.DataFrame,
        kr_rates: pd.DataFrame,
        spread: float,
        us_news: list = None,
        kr_news: list = None
    ) -> str:
        """
        Generate AI analysis of interest rate trends with news context.

        Args:
            us_rates: DataFrame with US rate data (date, us_rate)
            kr_rates: DataFrame with Korean rate data (date, kr_rate)
            spread: Current spread in basis points
            us_news: List of US news items
            kr_news: List of Korean news items

        Returns:
            Analysis text (3 sentences)
        """
        # Check cache first
        cache_key = self._get_cache_key(us_rates, kr_rates, us_news, kr_news)
        if cache_key in self._cache:
            logger.info("Returning cached analysis")
            return self._cache[cache_key]

        if not self.api_key:
            logger.warning("AI model not available, returning default message")
            return self._get_default_analysis(us_rates, kr_rates, spread)

        try:
            # Prepare data summary for prompt
            us_summary = self._format_rate_data(us_rates, "us_rate")
            kr_summary = self._format_rate_data(kr_rates, "kr_rate")

            # Format news data (Korean news only)
            kr_news_summary = self._format_news_data(kr_news)

            # Build prompt
            prompt = self.ANALYSIS_PROMPT.format(
                us_data=us_summary,
                kr_data=kr_summary,
                spread=f"{spread:.1f}",
                kr_news=kr_news_summary
            )

            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.MODEL_NAME,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }

            # Make API request
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    analysis = data["choices"][0]["message"]["content"].strip()

                    # Remove any thinking tags if present
                    if "<think>" in analysis:
                        analysis = analysis.split("</think>")[-1].strip()

                    # Validate response (should be approximately 3 sentences)
                    if len(analysis) < 50 or len(analysis) > 700:
                        logger.warning("Analysis length unexpected, using default")
                        analysis = self._get_default_analysis(us_rates, kr_rates, spread)

                    # Cache the result
                    self._cache[cache_key] = analysis
                    logger.info("Generated new AI analysis via Groq")

                    return analysis

            elif response.status_code == 429:
                logger.warning("Groq rate limit exceeded")
                return self._get_default_analysis(us_rates, kr_rates, spread)

            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"Groq API error: {response.status_code} - {error_msg}")
                return self._get_default_analysis(us_rates, kr_rates, spread)

        except requests.exceptions.Timeout:
            logger.error("Groq API timeout")
            return self._get_default_analysis(us_rates, kr_rates, spread)

        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return self._get_default_analysis(us_rates, kr_rates, spread)

    def _format_rate_data(self, df: pd.DataFrame, rate_col: str) -> str:
        """Format rate data for the prompt."""
        if df.empty:
            return "데이터 없음"

        # Get summary statistics
        latest = df.iloc[-1][rate_col] if len(df) > 0 else 0
        first = df.iloc[0][rate_col] if len(df) > 0 else 0
        change = latest - first
        high = df[rate_col].max()
        low = df[rate_col].min()

        # Get dates
        start_date = df.iloc[0]["date"].strftime("%Y-%m-%d") if len(df) > 0 else "N/A"
        end_date = df.iloc[-1]["date"].strftime("%Y-%m-%d") if len(df) > 0 else "N/A"

        return (
            f"기간: {start_date} ~ {end_date}\n"
            f"현재: {latest:.3f}%\n"
            f"기간 변동: {change:+.3f}%p\n"
            f"고점: {high:.3f}%, 저점: {low:.3f}%"
        )

    def _format_news_data(self, news_list: list) -> str:
        """Format news data for the prompt."""
        if not news_list or len(news_list) == 0:
            return "최신 뉴스 없음"

        news_texts = []
        for i, item in enumerate(news_list[:10], 1):  # Max 10 news items
            title = item.get('title', '')
            source = item.get('source', '')
            snippet = item.get('snippet', '')
            if title:
                if snippet:
                    news_texts.append(f"{i}. [{source}] {title}\n   → {snippet}")
                else:
                    news_texts.append(f"{i}. [{source}] {title}")

        return "\n".join(news_texts) if news_texts else "최신 뉴스 없음"

    def _get_cache_key(self, us_rates: pd.DataFrame, kr_rates: pd.DataFrame, us_news: list = None, kr_news: list = None) -> str:
        """Generate cache key based on latest data and Korean news."""
        us_latest = us_rates.iloc[-1]["date"].strftime("%Y%m%d") if not us_rates.empty else "none"
        kr_latest = kr_rates.iloc[-1]["date"].strftime("%Y%m%d") if not kr_rates.empty else "none"

        # Include latest Korean news timestamp in cache key
        news_key = "nonews"
        if kr_news and len(kr_news) > 0:
            latest_news_time = kr_news[0].get('published_at', '')[:13]  # YYYY-MM-DDTHH
            news_key = latest_news_time.replace('-', '').replace('T', '').replace(':', '')

        return f"analysis_{us_latest}_{kr_latest}_{news_key}"

    def _get_default_analysis(
        self,
        us_rates: pd.DataFrame,
        kr_rates: pd.DataFrame,
        spread: float
    ) -> str:
        """Generate a default analysis when AI is unavailable."""
        if us_rates.empty or kr_rates.empty:
            return "현재 금리 데이터를 불러올 수 없어 분석이 제공되지 않습니다. 잠시 후 다시 시도해 주세요."

        # Calculate basic metrics
        us_latest = us_rates.iloc[-1]["us_rate"]
        kr_latest = kr_rates.iloc[-1]["kr_rate"]
        us_change = us_rates.iloc[-1]["us_rate"] - us_rates.iloc[0]["us_rate"]
        kr_change = kr_rates.iloc[-1]["kr_rate"] - kr_rates.iloc[0]["kr_rate"]

        # Determine trend direction
        us_trend = "상승" if us_change > 0.05 else ("하락" if us_change < -0.05 else "보합")
        kr_trend = "상승" if kr_change > 0.05 else ("하락" if kr_change < -0.05 else "보합")

        sentence1 = (
            f"최근 30일간 미국 10년물 금리는 {us_latest:.2f}%로 {us_trend}세를 보이고 있으며, "
            f"한국 10년물 금리는 {kr_latest:.2f}%로 {kr_trend}세를 나타내고 있습니다."
        )

        if spread < 0:
            sentence2 = (
                f"현재 한미 금리차는 {abs(spread):.0f}bp 역전 상태로, "
                f"원화 약세 압력과 외국인 자금 유출 가능성에 주의가 필요합니다."
            )
        else:
            sentence2 = (
                f"현재 한미 금리차는 {spread:.0f}bp로, "
                f"연준과 한은의 통화정책 방향성에 따른 금리 변동성 확대에 유의해야 합니다."
            )

        return f"{sentence1} {sentence2}"

    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()
        logger.info("Analysis cache cleared")

    def chat(self, message: str, context: dict = None) -> str:
        """
        Chat with AI about interest rates.
        This method is kept for backward compatibility but redirects to ChatService.
        """
        if not self.api_key:
            return "AI 서비스를 사용할 수 없습니다. API 키를 확인해 주세요."

        try:
            # Format context
            context_text = "데이터 없음"
            if context:
                context_text = (
                    f"미국 10년물 금리: {context.get('us_rate', 'N/A')}%\n"
                    f"한국 10년물 금리: {context.get('kr_rate', 'N/A')}%\n"
                    f"스프레드: {context.get('spread', 'N/A')}bp"
                )

            system_prompt = f"""당신은 금리 및 채권 시장 전문 AI 어시스턴트입니다.
사용자의 질문에 친절하고 전문적으로 답변해 주세요.

현재 시장 상황:
{context_text}

답변 규칙:
- 한국어로 답변하세요
- 간결하고 명확하게 답변하세요 (최대 3-4문장)
- 금리, 채권, 통화정책 관련 질문에 집중하세요
- 투자 조언은 일반적인 정보 제공 수준으로만 하세요
- 구체적인 수치가 있으면 포함하세요

/no_think"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }

            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"].strip()
                    if "<think>" in content:
                        content = content.split("</think>")[-1].strip()
                    return content

            return "응답을 생성할 수 없습니다. 다시 시도해 주세요."

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"죄송합니다. 응답을 생성하는 중 오류가 발생했습니다: {str(e)[:100]}"


# Singleton instance
_ai_service_instance: Optional[AIAnalysisService] = None


def get_ai_service() -> AIAnalysisService:
    """Get or create the AI service singleton."""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIAnalysisService()
    return _ai_service_instance
