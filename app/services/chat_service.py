"""
Chat Service using Groq API with Qwen3 32B
Provides AI chat functionality with interest rate context and news data.
Uses direct HTTP requests to avoid library compatibility issues.
"""

import os
import logging
import requests
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatService:
    """Service for AI chat using Groq API with Qwen3 32B."""

    # Groq API endpoint
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    # Qwen3 32B model on Groq (free tier: 1,000 RPD, 30 RPM)
    MODEL_NAME = "qwen/qwen3-32b"

    # System prompt for chat
    SYSTEM_PROMPT = """당신은 금리 데이터 정리 도우미입니다.
아래 제공된 데이터와 뉴스만을 기반으로 답변하세요.

## 현재 금리 데이터 (실시간)
{market_context}

## 최신 뉴스
{news_context}

## 답변 규칙
1. 위에 제공된 데이터와 뉴스를 기반으로 답변하세요
2. 제공되지 않은 정보는 "해당 정보가 제공되지 않았습니다"라고 답변하세요
3. 숫자는 위 데이터에 있는 그대로만 인용하세요
4. 뉴스 정보 인용 시 실제 언론사명을 "[Reuters]", "[연합뉴스]" 등으로 표기하세요
5. 한국어로 답변하세요

## 출력 형식
- 마크다운 기호(**, #, - 등)를 사용하지 마세요
- 번호(1. 2. 3.)로 핵심 포인트를 나열하세요
- 각 포인트는 1-2문장으로 간결하게 작성하세요
- 마지막에 [요약] 한 줄을 추가하세요"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chat service with Groq API key."""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')

        if self.api_key:
            logger.info("Groq chat service initialized with Qwen3 32B (HTTP mode)")
        else:
            logger.warning("Groq API key not provided")

    def chat(
        self,
        message: str,
        rate_context: dict = None,
        us_news: list = None,
        kr_news: list = None
    ) -> str:
        """
        Chat with AI about interest rates.

        Args:
            message: User's chat message
            rate_context: Dict with us_rate, kr_rate, spread
            us_news: List of US news items
            kr_news: List of Korean news items

        Returns:
            AI response text
        """
        if not self.api_key:
            return "AI 채팅 서비스를 사용할 수 없습니다. GROQ_API_KEY를 확인해 주세요."

        try:
            # Format market context
            market_context = self._format_market_context(rate_context)

            # Format news context
            news_context = self._format_news_context(us_news, kr_news)

            # Build system prompt with context
            system_prompt = self.SYSTEM_PROMPT.format(
                market_context=market_context,
                news_context=news_context
            )

            # Prepare request
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
                "temperature": 0.5,
                "max_tokens": 2000
            }

            # Make API request
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            # Handle response
            if response.status_code == 200:
                data = response.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"].strip()
                    # Remove any thinking tags if present
                    if "<think>" in content:
                        content = content.split("</think>")[-1].strip()
                    return content
                return "응답을 생성할 수 없습니다. 다시 시도해 주세요."

            elif response.status_code == 429:
                return "요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요. (Groq 무료 티어: 30 RPM, 1,000 RPD)"

            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"Groq API error: {response.status_code} - {error_msg}")
                return f"죄송합니다. 응답 생성 중 오류가 발생했습니다."

        except requests.exceptions.Timeout:
            logger.error("Groq API timeout")
            return "응답 시간이 초과되었습니다. 다시 시도해 주세요."

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in chat: {error_msg}")
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다."

    def _format_market_context(self, rate_context: dict) -> str:
        """Format rate data for the prompt."""
        if not rate_context:
            return "현재 금리 데이터 없음"

        us_rate = rate_context.get('us_rate', 'N/A')
        kr_rate = rate_context.get('kr_rate', 'N/A')
        spread = rate_context.get('spread', 'N/A')

        # Format spread status
        spread_status = ""
        if spread != 'N/A' and isinstance(spread, (int, float)):
            if spread < 0:
                spread_status = f" (역전 상태, 원화 약세 압력)"
            else:
                spread_status = f" (정상 상태)"

        return (
            f"- 미국 10년물 국고채 금리: {us_rate}%\n"
            f"- 한국 10년물 국고채 금리: {kr_rate}%\n"
            f"- 한미 금리 스프레드: {spread}bp{spread_status}"
        )

    def _format_news_context(self, us_news: list, kr_news: list) -> str:
        """Format news data for the prompt."""
        news_parts = []

        # US News
        if us_news and len(us_news) > 0:
            news_parts.append("### 미국 금리 관련 뉴스")
            for i, item in enumerate(us_news[:7], 1):
                title = item.get('title', '')
                source = item.get('source', '')
                snippet = item.get('snippet', '')
                if title:
                    news_parts.append(f"{i}. [{source}] {title}")
                    if snippet:
                        news_parts.append(f"   요약: {snippet}")
        else:
            news_parts.append("### 미국 금리 관련 뉴스\n최신 뉴스 없음")

        news_parts.append("")  # Empty line

        # Korean News
        if kr_news and len(kr_news) > 0:
            news_parts.append("### 한국 금리 관련 뉴스")
            for i, item in enumerate(kr_news[:7], 1):
                title = item.get('title', '')
                source = item.get('source', '')
                snippet = item.get('snippet', '')
                if title:
                    news_parts.append(f"{i}. [{source}] {title}")
                    if snippet:
                        news_parts.append(f"   요약: {snippet}")
        else:
            news_parts.append("### 한국 금리 관련 뉴스\n최신 뉴스 없음")

        return "\n".join(news_parts)

    def is_available(self) -> bool:
        """Check if the chat service is available."""
        return self.api_key is not None


# Singleton instance
_chat_service_instance: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create the chat service singleton."""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
