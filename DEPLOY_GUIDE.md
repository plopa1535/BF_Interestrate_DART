# 🚀 Render 배포 가이드

Interest Rate Monitor를 Render에 무료로 배포하는 단계별 가이드입니다.

---

## 📋 사전 준비

1. **GitHub 계정** - https://github.com (없으면 가입)
2. **Render 계정** - https://render.com (GitHub로 가입 가능)

---

## Step 1: GitHub 저장소 생성

### 1-1. GitHub에서 새 저장소 만들기

1. https://github.com/new 접속
2. Repository name: `interest-rate-monitor`
3. **Public** 선택 (무료 플랜)
4. **Create repository** 클릭

### 1-2. 로컬에서 코드 업로드

압축 파일을 풀고 터미널에서 실행:

```bash
# 압축 해제
unzip interest-rate-monitor.zip
cd interest-rate-monitor

# Git 초기화
git init
git add .
git commit -m "Initial commit: Interest Rate Monitor"

# GitHub 연결 (YOUR_USERNAME을 본인 GitHub 아이디로 변경)
git remote add origin https://github.com/YOUR_USERNAME/interest-rate-monitor.git
git branch -M main
git push -u origin main
```

⚠️ **중요**: `.gitignore`가 `.env` 파일을 제외하므로 API 키는 GitHub에 업로드되지 않습니다.

---

## Step 2: Render에서 배포

### 2-1. Render 웹서비스 생성

1. https://dashboard.render.com 접속
2. **New +** → **Web Service** 클릭
3. **Connect a repository** → GitHub 연결
4. `interest-rate-monitor` 저장소 선택 → **Connect**

### 2-2. 서비스 설정

| 항목 | 값 |
|------|-----|
| **Name** | `interest-rate-monitor` (또는 원하는 이름) |
| **Region** | `Singapore (Southeast Asia)` 권장 |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT "app:create_app()"` |
| **Instance Type** | `Free` |

### 2-3. 환경 변수 설정 (⭐ 중요!)

**Environment** 섹션에서 **Add Environment Variable** 클릭:

| Key | Value |
|-----|-------|
| `FRED_API_KEY` | `7e404cd58cc495f3e540fa067c80d2db` |
| `ECOS_API_KEY` | `RLJFTFIFA0Q8P141UQYE` |
| `GEMINI_API_KEY` | `AIzaSyBsVp9hQMmCU72wEHy5xwx2ZwnfuLJPATc` |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `0` |
| `SECRET_KEY` | (Generate 버튼 클릭 또는 임의 문자열) |

### 2-4. 배포 시작

**Create Web Service** 클릭!

빌드 및 배포가 진행됩니다 (약 2-5분 소요).

---

## Step 3: 접속 확인

배포가 완료되면 Render가 URL을 제공합니다:

```
https://interest-rate-monitor-xxxx.onrender.com
```

이 URL로 어디서든 접속 가능합니다! 🎉

---

## 📌 추가 설정

### 커스텀 도메인 연결 (선택사항)

1. Render 대시보드 → 서비스 선택 → **Settings**
2. **Custom Domains** → **Add Custom Domain**
3. 본인 도메인 입력 후 DNS 설정

### 자동 배포

GitHub에 push하면 자동으로 재배포됩니다:

```bash
git add .
git commit -m "Update feature"
git push origin main
# → Render가 자동으로 감지하여 재배포
```

---

## ⚠️ 무료 플랜 제한사항

| 항목 | 제한 |
|------|------|
| **슬립 모드** | 15분 미사용 시 슬립 (첫 요청 시 30초 대기) |
| **월 사용량** | 750시간/월 |
| **대역폭** | 100GB/월 |

> 💡 **Tip**: 슬립 방지를 원하면 UptimeRobot(무료) 같은 서비스로 주기적 핑 가능

---

## 🔧 문제 해결

### 배포 실패 시

1. Render 대시보드 → **Logs** 탭 확인
2. 주로 발생하는 문제:
   - `requirements.txt` 패키지 버전 충돌
   - 환경 변수 누락
   - Python 버전 불일치

### 500 에러 발생 시

1. 환경 변수가 모두 설정되었는지 확인
2. Logs에서 에러 메시지 확인

---

## 📞 지원

문제가 있으면 Render 공식 문서를 참고하세요:
- https://render.com/docs

---

**배포 완료 후 URL을 공유하시면 확인해 드리겠습니다!** 🚀
