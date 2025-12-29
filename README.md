# 📊 Interest Rate Monitor

미국과 한국의 10년물 국고채 금리를 실시간으로 모니터링하는 Flask 기반 웹 애플리케이션입니다.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 주요 기능

1. **금리 시각화**: 최근 3개월간 미국/한국 10Y 국고채 금리 추이를 인터랙티브 차트로 제공
2. **스프레드 분석**: 한미 금리차(스프레드)를 막대 그래프로 시각화
3. **AI 분석**: Google Gemini 2.5 Flash를 활용한 금리 동향 분석 (2문장 요약)
4. **뉴스 피드**: 미국/한국 금리 관련 최신 뉴스 자동 수집

## 🛠 기술 스택

- **Backend**: Flask 3.0, Python 3.10+
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js 4.x
- **Data Sources**: 
  - FRED API (미국 금리)
  - 한국은행 ECOS API (한국 금리)
- **AI**: Google Gemini 2.5 Flash
- **News**: Google News RSS

## 📦 설치 방법

### 1. 저장소 클론 및 가상환경 생성

```bash
git clone <repository-url>
cd interest-rate-monitor

# 가상환경 생성
python -m venv interestratemonitoring
source interestratemonitoring/bin/activate  # Linux/Mac
# 또는
interestratemonitoring\Scripts\activate  # Windows
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 API 키를 입력합니다:

```bash
cp .env.example .env
```

```env
# .env 파일
FRED_API_KEY=your_fred_api_key_here
ECOS_API_KEY=your_ecos_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
FLASK_DEBUG=1
```

### 4. API 키 발급 방법

| API | 발급 URL | 비고 |
|-----|----------|------|
| FRED | https://fred.stlouisfed.org/docs/api/api_key.html | 미국 연준 경제데이터 |
| ECOS | https://ecos.bok.or.kr/ | 한국은행 경제통계시스템 |
| Gemini | https://makersuite.google.com/app/apikey | Google AI Studio |

## 🚀 실행 방법

### 개발 모드

```bash
python run.py
```

서버가 `http://localhost:5000`에서 시작됩니다.

### 프로덕션 모드

```bash
gunicorn -c gunicorn.conf.py "app:create_app()"
```

## 📡 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/rates` | 금리 데이터 조회 (days 파라미터로 기간 지정) |
| GET | `/api/v1/rates/latest` | 최신 금리 데이터 |
| GET | `/api/v1/analysis` | AI 분석 결과 |
| GET | `/api/v1/news` | 뉴스 피드 (country: us/kr/all) |
| GET | `/api/v1/health` | 서비스 상태 확인 |
| POST | `/api/v1/cache/clear` | 캐시 초기화 |

### 예시 응답

```json
{
  "status": "success",
  "timestamp": "2024-12-20T10:30:00",
  "data": {
    "rates": [
      {
        "date": "2024-12-19",
        "us_rate": 4.523,
        "kr_rate": 2.876,
        "spread": -164.7
      }
    ],
    "count": 90,
    "period_days": 90
  }
}
```

## 📁 프로젝트 구조

```
interest-rate-monitor/
├── app/
│   ├── __init__.py          # Flask 앱 팩토리
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py           # API 엔드포인트
│   └── services/
│       ├── __init__.py
│       ├── rate_service.py       # 금리 데이터 수집
│       ├── ai_analysis_service.py # AI 분석
│       └── news_service.py       # 뉴스 수집
├── static/
│   ├── css/
│   │   └── style.css        # 스타일시트
│   └── js/
│       ├── charts.js        # 차트 모듈
│       └── app.js           # 메인 앱 로직
├── templates/
│   └── index.html           # 메인 페이지
├── tests/
│   └── __init__.py
├── .env.example             # 환경 변수 템플릿
├── config.py                # 설정 파일
├── gunicorn.conf.py         # Gunicorn 설정
├── requirements.txt         # 패키지 목록
├── run.py                   # 실행 스크립트
└── README.md
```

## 🔧 설정 옵션

### 캐시 TTL 설정 (config.py)

| 설정 | 기본값 | 설명 |
|------|--------|------|
| RATE_CACHE_TTL | 3600 | 금리 데이터 캐시 (1시간) |
| ANALYSIS_CACHE_TTL | 21600 | AI 분석 캐시 (6시간) |
| NEWS_CACHE_TTL | 1800 | 뉴스 캐시 (30분) |

## 🐳 Docker 배포 (선택사항)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:create_app()"]
```

```bash
docker build -t interest-rate-monitor .
docker run -p 5000:5000 --env-file .env interest-rate-monitor
```

## 📝 라이선스

MIT License

## 🙏 Acknowledgments

- [FRED](https://fred.stlouisfed.org/) - Federal Reserve Economic Data
- [한국은행 ECOS](https://ecos.bok.or.kr/) - 한국은행 경제통계시스템
- [Google Gemini](https://ai.google.dev/) - AI 분석
- [Chart.js](https://www.chartjs.org/) - 차트 라이브러리
