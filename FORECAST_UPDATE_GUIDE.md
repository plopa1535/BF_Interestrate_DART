# 애널리스트 전망치 수정 가이드

## 개요
웹 화면 하단의 "Analyst Forecast" 섹션에 표시되는 향후 12개월 금리 전망치를 수정하는 방법입니다.

---

## 전망치 파일 위치

```
interest-rate-monitor/
└── static/
    └── data/
        └── forecast.json   ← 이 파일을 수정
```

---

## JSON 파일 구조

```json
{
  "updated_at": "2025-12-20",
  "source": "증권사 컨센서스",
  "forecasts": [
    {
      "month": "2026-01",
      "us_rate": 4.35,
      "kr_rate": 2.75
    },
    {
      "month": "2026-02",
      "us_rate": 4.30,
      "kr_rate": 2.70
    }
    // ... 12개월 데이터
  ]
}
```

### 필드 설명

| 필드 | 설명 | 예시 |
|------|------|------|
| `updated_at` | 데이터 업데이트 날짜 | `"2025-12-20"` |
| `source` | 데이터 출처 | `"증권사 컨센서스"` |
| `month` | 전망 월 (YYYY-MM 형식) | `"2026-01"` |
| `us_rate` | 미국 10년물 금리 전망 (%) | `4.35` |
| `kr_rate` | 한국 10년물 금리 전망 (%) | `2.75` |

---

## 수정 방법 (단계별)

### Step 1: forecast.json 파일 열기

VS Code 또는 메모장에서 아래 파일을 엽니다:
```
interest-rate-monitor/static/data/forecast.json
```

### Step 2: 데이터 수정

1. **업데이트 날짜 변경**
   ```json
   "updated_at": "2025-12-21",
   ```

2. **출처 변경 (필요시)**
   ```json
   "source": "NH투자증권 리서치",
   ```

3. **전망치 수정**
   ```json
   {
     "month": "2026-01",
     "us_rate": 4.40,    ← 미국 금리 수정
     "kr_rate": 2.80     ← 한국 금리 수정
   }
   ```

### Step 3: 파일 저장

`Ctrl + S`로 파일을 저장합니다.

### Step 4: GitHub에 Push

터미널(명령 프롬프트)에서 실행:

```bash
cd interest-rate-monitor
git add .
git commit -m "Update forecast data"
git push
```

또는 한 줄로:
```bash
git add . && git commit -m "Update forecast data" && git push
```

### Step 5: 배포 확인

- Render가 자동으로 재배포합니다 (약 3-5분 소요)
- 또는 Render Dashboard에서 `Manual Deploy` 클릭

### Step 6: 웹사이트 확인

https://interest-rate-monitor.onrender.com 에서 변경사항 확인

---

## 수정 예시

### 예시: 2026년 1월 전망치를 US 4.50%, KR 2.90%로 변경

**변경 전:**
```json
{
  "month": "2026-01",
  "us_rate": 4.35,
  "kr_rate": 2.75
}
```

**변경 후:**
```json
{
  "month": "2026-01",
  "us_rate": 4.50,
  "kr_rate": 2.90
}
```

---

## 주의사항

1. **JSON 문법 주의**
   - 마지막 항목 뒤에 쉼표(,) 없어야 함
   - 문자열은 큰따옴표(") 사용
   - 숫자는 따옴표 없이 입력

2. **올바른 형식:**
   ```json
   {
     "month": "2026-01",
     "us_rate": 4.35,
     "kr_rate": 2.75
   }
   ```

3. **잘못된 형식:**
   ```json
   {
     "month": "2026-01",
     "us_rate": "4.35",    ← 숫자에 따옴표 X
     "kr_rate": 2.75,      ← 마지막 항목 뒤 쉼표 X
   }
   ```

---

## JSON 문법 오류 확인

수정 후 문법 오류가 있는지 확인하려면:
1. https://jsonlint.com/ 접속
2. forecast.json 내용 붙여넣기
3. "Validate JSON" 클릭
4. "Valid JSON" 메시지 확인

---

## 빠른 참조

```bash
# 전망치 수정 후 배포 명령어
cd interest-rate-monitor
git add . && git commit -m "Update forecast data" && git push
```

---

*Last Updated: 2025-12-21*
