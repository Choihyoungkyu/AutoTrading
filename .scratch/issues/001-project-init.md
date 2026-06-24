# 프로젝트 초기화 & 데이터 수집 기본 구조

## What to build

팀이 처음 3일간 초석을 다지는 작업. Python 백엔드 프로젝트를 세팅하고, 실제 증권 데이터를 가져올 수 있는 라이브러리들을 연동한다. 이후 모든 분석 엔진이 이 데이터 기반 위에서 작동하게 된다.

**End-to-end 동작:**
- `pip install` 후 Python 코드에서 PYKRX로 국내 주식 시세 데이터 조회 가능
- yfinance로 해외 주식 및 뉴스 조회 가능  
- SQLite 또는 CSV로 수집한 데이터를 저장하고 불러올 수 있음
- Flask/FastAPI 기본 서버 구동 가능

## Acceptance criteria

- [ ] Python 프로젝트 초기화 (requirements.txt, .gitignore, 폴더 구조)
- [ ] PYKRX 라이브러리로 삼성전자(005930) 시세 데이터 조회 테스트 완료
- [ ] yfinance 라이브러리로 AAPL, TSLA 시세 데이터 조회 테스트 완료
- [ ] SQLite 또는 CSV로 데이터 저장 및 로드 기능 구현
- [ ] Flask 또는 FastAPI 기본 서버 구동 (`python main.py` → http://localhost:5000)
- [ ] 데이터 수집 모듈 테스트 (고정 종목으로 데이터 수집 가능 확인)

## Blocked by

None - can start immediately

## User Stories

- 13: 데이터 수집 모듈이 PYKRX(국내)와 yfinance(해외)에서 안정적으로 데이터를 가져오기
- 14: 각 분석 모듈이 독립적으로 테스트 가능하기
