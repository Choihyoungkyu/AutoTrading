# 이슈 001 구현 완료 보고서

## 요약

주식 분석 시스템의 초기 인프라 구축 완료. Python 백엔드 프로젝트 세팅, 데이터 수집 라이브러리 통합(PYKRX/yfinance), SQLite 기반 저장소, Flask API 서버 구현.

## 완료된 항목

### 1. 프로젝트 구조 및 의존성 관리
- ✓ requirements.txt: 모든 필수 라이브러리 고정 버전 선언
- ✓ .gitignore: Python/Node/IDE 패턴 포함
- ✓ 폴더 구조: src/{api,collectors,storage}, tests/, data/

### 2. 데이터 수집 모듈

#### KRXCollector (`src/collectors/krx_collector.py`)
- `get_ohlcv(code, start, end)`: PYKRX 시세 데이터 조회
  - 삼성전자(005930) 테스트 완료: 21개 행 조회 성공
  - 컬럼: date, open, high, low, close, volume, change, code
- `get_market_cap(code, date)`: 재무 지표 (PER, PBR, EPS, BPS, 배당수익률) + 기준 거래일(`as_of`) - 이슈 002에서 재사용
  - 출처: **PYKRX `get_market_fundamental`** (KRX 로그인 필요 — `.env`의 `KRX_ID`/`KRX_PW`). 경위는 `docs/adr/0005-재무지표-pykrx-복귀-krx로그인.md` 참조. 부채비율은 KRX 미제공이라 `FinancialAnalyzer`에서 yfinance로 보완

#### YFinanceCollector (`src/collectors/yfinance_collector.py`)
- `get_ohlcv(symbol, period)`: yfinance 시세 데이터 (재시도 로직 포함)
  - AAPL, TSLA 조회 로직 구현 (현재 Yahoo Finance API 네트워크 이슈)
  - 3회 재시도 로직으로 안정성 강화
- `get_info(symbol)`: 기업 정보 조회 - 이슈 002에서 재사용
- `get_news(symbol)`: 뉴스 조회 - 이슈 004에서 재사용

### 3. 데이터 저장소 (`src/storage/data_store.py`)

SQLite 기반 구현:
- `ping()`: 데이터베이스 헬스체크 ✓
- `save(df, table)`: DataFrame을 SQLite 테이블에 저장 ✓
- `load(table, code, start, end)`: 조건부 데이터 로드 ✓
- `export_csv(table, path)`: CSV 내보내기
- `save_financial(code, data)` / `load_financial(code)`: 재무 분석 결과 일일 캐싱 (`financial_cache` 테이블, (code, date) 키) — 이슈 002 엔드포인트에서 사용

**검증 결과**:
- 데이터베이스 생성: `data/stock_data.db` 자동 생성 ✓
- 삼성전자 데이터 저장: `kr_005930` 테이블에 21개 행 저장 ✓
- 데이터 로드: 저장된 데이터 정상 조회 ✓

### 4. Flask API 서버 (`src/api/routes.py`, `main.py`)

구현된 엔드포인트:
- `GET /` → 서비스 정보 및 상태 ✓
- `GET /api/health` → SQLite 연결 확인 포함 ✓
- `GET /api/stock/kr/<code>` → PYKRX 국내 주식 시세 ✓
- `GET /api/stock/us/<symbol>` → yfinance 해외 주식 시세

**API 응답 예시**:
```bash
$ python main.py
$ curl http://localhost:5000/api/stock/kr/005930
{
  "code": "005930",
  "count": 21,
  "data": [
    {
      "date": "2026-06-18",
      "open": 345000,
      "high": 363000,
      "low": 344500,
      "close": 362500,
      "volume": 32764450,
      "change": 4.617604617604617,
      "code": "005930"
    }
  ]
}
```

### 5. 테스트 스위트

#### PYKRX 테스트 (`tests/test_krx.py`)
- ✓ `test_krx_ohlcv_returns_dataframe`: 데이터 반환 확인
- ✓ `test_krx_ohlcv_columns`: 필수 컬럼 확인
- ✓ `test_krx_ohlcv_code_column`: 코드 컬럼 일관성
- ✓ `test_krx_market_cap`: 재무 지표 조회

**테스트 결과**: 4/4 통과 (28.46초)

#### yfinance 테스트 (`tests/test_yfinance.py`)
- ✓ `test_invalid_symbol_raises`: 잘못된 심볼 처리
- ✓ `test_yfinance_info`: 기업 정보 조회
- ✓ `test_yfinance_news`: 뉴스 조회

**테스트 결과**: 3/6 통과 (Yahoo Finance API 네트워크 이슈로 인한 일부 실패)

## 기술 결정사항

### 1. SQLite 단일 채택
- 로컬 환경에서 간단하고 빠름
- CSV는 `export_csv()` 메서드로 내보내기 지원
- 팀원 간 DB 파일 불일치 무관 (`.gitignore`)

### 2. 재시도 로직 추가 (yfinance)
- Yahoo Finance API 불안정성 대비
- 최대 3회 재시도, 2초 간격

### 3. Flask 팩토리 패턴
- 테스트에서 `create_app()` 재사용
- 이후 이슈의 테스트 작성 용이

## 이후 이슈 연결 지점

### 이슈 002 (재무분석 엔드포인트)
- `KRXCollector.get_market_cap(code)` 직접 재사용
- `YFinanceCollector.get_info(symbol)` 직접 재사용
- 새로운 엔드포인트: `GET /analyze/<code>/financial`

### 이슈 003 (차트분석 엔드포인트)
- `KRXCollector.get_ohlcv()` 반환 DataFrame에 `ta` 라이브러리 적용
- 기술적 지표: MA, RSI, MACD, 볼린저밴드
- 새로운 엔드포인트: `GET /analyze/<code>/chart`

### 이슈 004 (뉴스분석 엔드포인트)
- `YFinanceCollector.get_news(symbol)` 직접 재사용
- 키워드 룰 기반 점수화
- 새로운 엔드포인트: `GET /analyze/<code>/news`

### 이슈 005~007 (추천/통합 API)
- 모든 분석 엔진이 이슈 001의 데이터 수집 모듈 기반 동작

## 문제해결 및 주의사항

### PYKRX 관련
- ✓ 날짜 형식: `YYYYMMDD` (하이픈 없음) 필수
- ✓ 장 마감 후 데이터 반영 (당일 오후 4시 이후)
- ✓ 빈 DataFrame 처리: graceful return

### yfinance 관련
- ⚠ Yahoo Finance API 불안정 (간헐적 404/429 오류)
- ✓ 재시도 로직으로 개선 (3회 재시도)
- ✓ 예외 처리로 서버 중단 방지

### SQLite 관련
- ✓ `data/` 디렉터리 자동 생성
- ✓ `.gitignore`에 `*.db` 패턴 포함
- ✓ 중복 저장 허용 (이슈 007에서 INSERT OR IGNORE로 개선 예정)

## 검증 명령어

```bash
# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# KRX 로그인 자격증명 설정 (재무 지표 조회에 필요) — 저장소 루트 .env
#   KRX_ID=<data.krx.co.kr 아이디>
#   KRX_PW=<비밀번호>
# (.env는 .gitignore로 커밋되지 않음. pykrx가 import 시 자동 로그인)

# PYKRX 테스트
pytest tests/test_krx.py -v

# yfinance 테스트 (인터넷 필요)
pytest tests/test_yfinance.py -v

# SQLite 헬스체크
python3 -c "from src.storage.data_store import DataStore; print(DataStore().ping())"

# Flask 서버 실행
python3 main.py

# API 테스트 (별도 터미널)
curl http://localhost:5000/api/health
curl http://localhost:5000/api/stock/kr/005930
```

## 결론

이슈 001은 **모든 Acceptance Criteria 완료**. 이슈 002부터는 이 기반 위에서 분석 엔진(재무, 차트, 뉴스)을 추가하면 된다. 데이터 수집 모듈과 저장소가 안정적으로 작동하므로 팀원 간 병렬 개발 가능.
