# Interest Rate Monitor 배포 가이드

## 개요
이 문서는 Interest Rate Monitor 웹 애플리케이션을 Render 클라우드 플랫폼에 배포하는 전체 과정을 설명합니다.

---

## 1. GitHub 저장소 설정

### 1.1 GitHub 저장소 생성
1. [GitHub](https://github.com)에 로그인
2. 우측 상단 `+` 버튼 클릭 → `New repository` 선택
3. Repository name: `Interest-Rate-Monitor`
4. Public 또는 Private 선택
5. `Create repository` 클릭

### 1.2 로컬 프로젝트를 GitHub에 Push

```bash
# 프로젝트 디렉토리로 이동
cd interest-rate-monitor

# Git 초기화
git init

# Git 사용자 정보 설정 (최초 1회)
git config user.email "your-email@example.com"
git config user.name "Your Name"

# 모든 파일 스테이징
git add .

# 첫 번째 커밋
git commit -m "Initial commit: Interest Rate Monitor"

# 기본 브랜치를 main으로 설정
git branch -M main

# 원격 저장소 연결
git remote add origin https://github.com/YOUR_USERNAME/Interest-Rate-Monitor.git

# GitHub에 Push
git push -u origin main
```

---

## 2. Render 배포 설정

### 2.1 Render 계정 생성 및 로그인
1. [Render](https://render.com) 접속
2. GitHub 계정으로 회원가입/로그인

### 2.2 새 웹 서비스 생성
1. Dashboard에서 `New +` 버튼 클릭
2. `Web Service` 선택
3. GitHub 저장소 연결:
   - `Connect a repository` 클릭
   - `Interest-Rate-Monitor` 저장소 선택

### 2.3 서비스 설정

| 항목 | 설정값 | 설명 |
|------|--------|------|
| **Name** | `interest-rate-monitor` | 서비스 이름 (URL에 사용됨) |
| **Region** | `Oregon (US West)` 또는 `Singapore` | 서버 위치 |
| **Branch** | `main` | 배포할 브랜치 |
| **Runtime** | `Python 3` | 런타임 환경 |
| **Build Command** | `pip install -r requirements.txt` | 의존성 설치 명령 |
| **Start Command** | `python run.py` | 서버 시작 명령 |
| **Instance Type** | `Free` | 요금제 (무료/유료) |

### 2.4 환경 변수 설정 (Environment Variables)

`Environment` 섹션에서 다음 변수들을 추가:

| Key | Value | 설명 |
|-----|-------|------|
| `FRED_API_KEY` | `your_fred_api_key` | 미국 금리 데이터 API 키 |
| `ECOS_API_KEY` | `your_ecos_api_key` | 한국은행 ECOS API 키 |
| `GEMINI_API_KEY` | `your_gemini_api_key` | Google Gemini AI API 키 |
| `FLASK_ENV` | `production` | Flask 환경 설정 |

### 2.5 배포 실행
1. 모든 설정 완료 후 `Create Web Service` 클릭
2. 자동으로 빌드 및 배포 시작
3. 배포 완료 시 URL 제공: `https://interest-rate-monitor.onrender.com`

---

## 3. 배포 후 업데이트 방법

코드 수정 후 재배포는 매우 간단합니다:

```bash
# 변경사항 스테이징
git add .

# 커밋
git commit -m "Update: 변경 내용 설명"

# GitHub에 Push (자동 재배포 트리거)
git push
```

> **Note**: GitHub에 push하면 Render가 자동으로 감지하여 재배포를 시작합니다.

---

## 4. 주요 파일 구조

```
interest-rate-monitor/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   └── services/
│       ├── rate_service.py      # 금리 데이터 수집
│       ├── news_service.py      # 뉴스 수집
│       └── ai_analysis_service.py  # Gemini AI 분석
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       └── charts.js
├── templates/
│   └── index.html
├── .env                  # 로컬 환경 변수 (git에 포함 안됨)
├── .gitignore
├── requirements.txt      # Python 의존성
├── run.py               # 서버 실행 파일
└── CLAUDE.md            # 프로젝트 문서
```

---

## 5. API 키 발급 방법

### FRED API Key
1. [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html) 접속
2. 계정 생성 후 API Key 발급

### ECOS API Key
1. [한국은행 경제통계시스템](https://ecos.bok.or.kr/) 접속
2. 회원가입 후 API 인증키 신청

### Gemini API Key
1. [Google AI Studio](https://aistudio.google.com/) 접속
2. Google 계정으로 로그인
3. API Key 생성

---

## 6. 문제 해결

### 배포 실패 시
1. Render Dashboard에서 `Logs` 탭 확인
2. 에러 메시지 분석
3. 일반적인 문제:
   - `requirements.txt` 누락된 패키지
   - 환경 변수 미설정
   - Python 버전 불일치

### 무료 티어 제한사항
- 15분간 요청이 없으면 서비스 슬립 모드 진입
- 첫 요청 시 약 30초~1분 대기 시간 발생
- 유료 플랜 업그레이드로 해결 가능

---

## 7. 배포 URL

- **Production URL**: https://interest-rate-monitor.onrender.com
- **GitHub Repository**: https://github.com/plopa1535/Interest-Rate-Monitor

---

*Last Updated: 2025-12-20*
