"""
DART API Service
금융감독원 전자공시시스템(DART)에서 보험사 재무 데이터 조회 서비스
"""

import os
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from statistics import median
from typing import Dict, List, Optional, Tuple
import logging

import requests
import pandas as pd
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# ============================================================================
# 캐시 설정
# ============================================================================
dart_cache = TTLCache(maxsize=256, ttl=21600)  # 6시간
corp_code_cache = TTLCache(maxsize=10, ttl=86400)  # 24시간

# ============================================================================
# 회사 매핑 (corp_code 하드코딩)
# ============================================================================
COMPANY_MAP = {
    'samsung': {'name': '삼성생명', 'corp_code': '00126256'},
    'hanwha': {'name': '한화생명', 'corp_code': '00113058'},
    'kyobo': {'name': '교보생명', 'corp_code': '00112882'},
    'shinhan': {'name': '신한생명', 'corp_code': '00137517'}
}


class DartService:
    """DART API 서비스 클래스"""

    def __init__(self, api_key: str):
        """
        DART 서비스 초기화

        Args:
            api_key: DART API 키
        """
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"

    def get_equity_data(self, company_id: str, year_count: int = 3) -> List[Dict]:
        """
        DART에서 별도 재무제표 기준 자본총계 조회

        Args:
            company_id: 회사 ID (samsung, hanwha, kyobo, shinhan)
            year_count: 조회할 연도 수 (기본 3년)

        Returns:
            분기별 재무 데이터 리스트
            [
                {
                    'quarter': '2024-03-31',
                    'equity': 12345678900000,
                    'asset': 98765432100000,
                    'liability': 86419753200000
                },
                ...
            ]
        """
        cache_key = f"equity_{company_id}_{year_count}"
        if cache_key in dart_cache:
            logger.info(f"DART 캐시 히트: {cache_key}")
            return dart_cache[cache_key]

        if not self.api_key:
            raise ValueError("DART_API_KEY가 설정되지 않았습니다.")

        if company_id not in COMPANY_MAP:
            raise ValueError(f"지원하지 않는 회사입니다: {company_id}")

        corp_code = COMPANY_MAP[company_id]['corp_code']
        current_year = datetime.now().year

        # 분기 데이터 수집
        quarters_data = []

        for year in range(current_year - year_count, current_year + 1):
            # 보고서 유형별 조회 (1분기, 반기, 3분기, 사업)
            report_codes = [
                ('11013', f'{year}-03-31', '1Q'),
                ('11012', f'{year}-06-30', '2Q'),
                ('11014', f'{year}-09-30', '3Q'),
                ('11011', f'{year}-12-31', '4Q'),
            ]

            for reprt_code, quarter_end, quarter_name in report_codes:
                # 미래 분기는 건너뛰기
                quarter_date = datetime.strptime(quarter_end, '%Y-%m-%d')
                if quarter_date > datetime.now():
                    continue

                try:
                    # 단일회사 주요계정 조회 API
                    url = f"{self.base_url}/fnlttSinglAcnt.json"
                    params = {
                        'crtfc_key': self.api_key,
                        'corp_code': corp_code,
                        'bsns_year': str(year),
                        'reprt_code': reprt_code
                    }

                    response = requests.get(url, params=params, timeout=30)
                    data = response.json()

                    if data.get('status') == '000' and data.get('list'):
                        quarter_item = {'quarter': quarter_end}

                        for item in data['list']:
                            account_nm = item.get('account_nm', '')
                            fs_div = item.get('fs_div', '')  # OFS: 별도, CFS: 연결

                            # 별도 재무제표만 사용
                            if fs_div != 'OFS':
                                continue

                            amount_str = item.get('thstrm_amount', '0')
                            if not amount_str or amount_str == '-':
                                continue

                            amount = int(amount_str.replace(',', ''))

                            # 자본총계
                            if '자본총계' in account_nm or account_nm == '자본 총계':
                                quarter_item['equity'] = amount
                            # 자산총계
                            elif '자산총계' in account_nm or account_nm == '자산 총계':
                                quarter_item['asset'] = amount
                            # 부채총계
                            elif '부채총계' in account_nm or account_nm == '부채 총계':
                                quarter_item['liability'] = amount

                        if 'equity' in quarter_item:
                            quarters_data.append(quarter_item)

                except Exception as e:
                    logger.warning(f"DART 조회 오류 ({year} {quarter_name}): {e}")
                    continue

        # 중복 제거 및 정렬
        df = pd.DataFrame(quarters_data)
        if df.empty:
            raise ValueError("자본총계 데이터를 찾을 수 없습니다.")

        df = df.drop_duplicates(subset=['quarter']).sort_values('quarter')
        df = df.tail(year_count * 4)  # 최근 N년치만

        result = df.to_dict('records')
        dart_cache[cache_key] = result

        logger.info(f"DART 데이터 조회 성공: {company_id}, {len(result)}개 분기")
        return result

    def calculate_duration(
        self,
        equity_data: List[Dict],
        rate_data: Dict[str, float]
    ) -> Tuple[List[Optional[float]], Optional[float]]:
        """
        듀레이션(금리 민감도) 계산

        Args:
            equity_data: 분기별 자본총계 데이터
            rate_data: 분기별 금리 데이터 {'2024-03-31': 4.5, ...}

        Returns:
            (duration_series, duration_summary)
            - duration_series: 분기별 듀레이션 리스트
            - duration_summary: 중앙값 기준 요약 듀레이션
        """
        if len(equity_data) < 2:
            return [], None

        quarters = [item['quarter'] for item in equity_data]
        equity_levels = [item['equity'] for item in equity_data]

        # 자본 변화율 계산 (QoQ)
        equity_qoq = [None]
        for i in range(1, len(equity_levels)):
            if equity_levels[i-1] and equity_levels[i-1] != 0:
                change = (equity_levels[i] / equity_levels[i-1]) - 1
                equity_qoq.append(change)
            else:
                equity_qoq.append(None)

        # 금리 변화 계산
        rate_change = [None]
        rate_levels = [rate_data.get(q) for q in quarters]

        for i in range(1, len(rate_levels)):
            if rate_levels[i] is not None and rate_levels[i-1] is not None:
                # 퍼센트 단위를 소수로 변환 (4.5% -> 0.045)
                change = (rate_levels[i] / 100) - (rate_levels[i-1] / 100)
                rate_change.append(change)
            else:
                rate_change.append(None)

        # 듀레이션 계산: D = ΔEquity / ΔRate
        duration_series = []
        valid_durations = []

        for i in range(len(equity_qoq)):
            if i == 0 or equity_qoq[i] is None or rate_change[i] is None:
                duration_series.append(None)
            elif rate_change[i] == 0:
                duration_series.append(None)
            else:
                d = equity_qoq[i] / rate_change[i]
                # 이상치 클리핑 (±100 범위로 제한)
                d_clipped = max(min(d, 100), -100)
                duration_series.append(round(d_clipped, 2))
                valid_durations.append(d_clipped)

        # Summary는 median 사용 (강건성)
        summary = round(median(valid_durations), 2) if valid_durations else None

        return duration_series, summary

    def get_company_list(self) -> List[Dict]:
        """
        분석 가능한 회사 목록 반환

        Returns:
            [
                {"id": "samsung", "name": "삼성생명"},
                ...
            ]
        """
        return [
            {"id": company_id, "name": info['name']}
            for company_id, info in COMPANY_MAP.items()
        ]


# ============================================================================
# 서비스 인스턴스 생성 함수
# ============================================================================
_dart_service_instance = None


def get_dart_service() -> DartService:
    """
    DART 서비스 싱글톤 인스턴스 반환

    Returns:
        DartService 인스턴스
    """
    global _dart_service_instance

    if _dart_service_instance is None:
        api_key = os.getenv('DART_API_KEY', '')
        _dart_service_instance = DartService(api_key)
        logger.info("DART 서비스 초기화 완료")

    return _dart_service_instance
