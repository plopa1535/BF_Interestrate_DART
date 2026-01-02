# 금리 모니터링 웹앱 개발 대화 기록

## 세션 요약

### 프로젝트 개요
- **프로젝트명**: BF_Interestrate_DART (금리 모니터링 웹앱)
- **기술 스택**: Flask, Gunicorn, Chart.js, Groq API (Qwen3 32B)
- **배포**: Render

---

## 주요 작업 내역

### 1. 한국 뉴스 쿼리에 미국 금리 관련 검색어 추가
**파일**: `app/services/news_service.py`

```python
KR_QUERIES = [
    "한국 국고채 금리",
    "한국은행 기준금리",
    "채권시장 금리",
    "미국 금리 인하",  # 추가됨
    "연준 금리"        # 추가됨
]
```

**목적**: 한국 뉴스 소스에서 미국 금리 관련 소식도 가져오기 위함

---

### 2. 뉴스 Snippet 추가
**파일**: `app/services/ai_analysis_service.py`

AI 분석 프롬프트에 뉴스 제목뿐만 아니라 snippet(요약)도 포함하도록 수정:

```python
def _format_news_data(self, news_list: list) -> str:
    news_texts = []
    for i, item in enumerate(news_list[:10], 1):
        title = item.get('title', '')
        source = item.get('source', '')
        snippet = item.get('snippet', '')
        if title:
            if snippet:
                news_texts.append(f"{i}. [{source}] {title}\n   → {snippet}")
            else:
                news_texts.append(f"{i}. [{source}] {title}")
    return "\n".join(news_texts) if news_texts else "최신 뉴스 없음"
```

**목적**: AI가 뉴스 내용을 더 잘 이해할 수 있도록 context 제공

---

### 3. Fed Funds Rate 기능 추가 후 롤백

#### 추가했던 기능 (이후 제거됨):
- `rate_service.py`: `get_fed_funds_rate()`, `get_fed_rate_changes()` 함수
- `api.py`: `fed_rate_info`를 분석 엔드포인트에 추가
- `ai_analysis_service.py`: Fed rate 정보를 프롬프트에 포함

#### 롤백 이유:
사용자 요청으로 Fed Funds Rate 관련 기능 전체 제거

#### 최종 상태:
- FRED API에서 Fed Funds Rate (DFF) 데이터를 가져오는 기능 제거
- AI 분석 프롬프트에서 Fed 기준금리 섹션 제거
- 뉴스 snippet 기능은 유지

---

## 현재 AI 분석 프롬프트

```python
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
```

---

## Git 커밋 히스토리 (이번 세션)

1. 한국 뉴스 쿼리에 미국 금리 검색어 추가
2. 뉴스 snippet을 AI 분석에 추가
3. Fed Funds Rate 기능 추가
4. **Fed Funds Rate 기능 제거 (롤백)** - 커밋: `6c79ed6`

---

## 참고 사항

### 현재 미국 기준금리
- **4.25% ~ 4.50%** (2024년 12월 FOMC에서 25bp 인하)

### 캐싱 전략
- Rate 데이터: 1시간 TTL
- AI 분석: 6시간 TTL
- 뉴스: 30분 TTL

### API 키 (Render 환경변수)
- `FRED_API_KEY`: 미국 금리 데이터
- `ECOS_API_KEY`: 한국 금리 데이터
- `GROQ_API_KEY`: AI 분석 (Qwen3 32B)

---

## 파일 구조

```
BF_Interestrate_DART/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   └── api.py
│   └── services/
│       ├── rate_service.py
│       ├── ai_analysis_service.py
│       ├── news_service.py
│       ├── chat_service.py
│       └── dart_service.py
├── static/
│   ├── css/
│   ├── js/
│   └── data/
├── templates/
│   └── index.html
├── run.py
├── gunicorn.conf.py
└── requirements.txt
```

---

*저장일시: 2025-12-31*
