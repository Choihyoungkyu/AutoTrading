# ADR 0005: 재무 지표를 pykrx(KRX 로그인)로 복귀

**상태**: 채택됨 — ADR 0004(네이버 금융 전환)를 대체(supersede)함

## 맥락

ADR 0004에서 KRX 로그인을 피하려고 재무 지표를 네이버 금융 스크래핑으로 옮겼다.
이후 두 가지가 확인되었다.

- 네이버 값이 삼성증권(FnGuide)과 달라 보였는데, 분석 결과 **재무 기준은 동일(둘 다
  연결재무제표, BPS ≈ 72,000)**했고 차이는 "현재가 ÷ 2026.03 실적" vs "분기말 시점
  스냅샷"이라는 **주가 기준 시점** 때문이었다.
- 사용자가 KRX 정보데이터시스템(data.krx.co.kr) **로그인 자격증명을 제공**했고,
  pykrx `get_market_fundamental`이 정상 동작함을 검증했다.

KRX는 `get_market_fundamental(date, date, code)` 형태로 **특정 시점 조회**가 가능하고,
공식 데이터 소스라는 장점이 있다. 다만 KRX 수치는 **별도재무제표(별도) 기준**이라
연결 기준(네이버·삼성증권)과 EPS/BPS/PER이 다르다.

## 결정

재무 지표 수집을 **pykrx `get_market_fundamental`로 복귀**한다.

- `KRX_ID` / `KRX_PW`를 저장소 루트 `.env`에 저장한다(`.gitignore`로 커밋 제외).
- pykrx는 **import 시점에 로그인**하므로, `krx_collector.py`에서 pykrx import 이전에
  `dotenv.load_dotenv()`를 호출해 환경변수를 먼저 로드한다.
- `get_market_cap`은 PER/PBR/EPS/BPS/배당수익률(DIV)과 기준 거래일(`as_of`)을 반환한다.
  `date` 인자를 주면 해당 시점, 없으면 최근 영업일 기준값을 가져온다.
- **추정(Forward) PER**: KRX 미제공 → 표시 제거.
- **부채비율**: KRX 미제공 → 네이버 작업 이전의 `yfinance debtToEquity`로 복귀.
- 시세(OHLCV)는 기존대로 pykrx 경로 유지.

## 결과

**긍정**
- 공식 KRX 소스 사용. `date` 파라미터로 시점별(분기말 등) 조회 가능.
- 네이버 HTML 구조 의존 제거(파싱 깨짐 위험 해소).

**부정 / 트레이드오프**
- **KRX는 별도재무 기준**이라 EPS/BPS/PER이 연결 기준(삼성증권·네이버)과 다르다
  (예: BPS 63,997 vs 연결 ≈ 72,000, PER 51.55). 삼성증권 수치와 일치하지 않는다.
- **자격증명 필요**: `KRX_ID`/`KRX_PW`(.env) 미설정 시 재무 조회가 빈 값이 된다.
- **추정 PER 상실**, **부채비율은 다시 yfinance D/E**(표준 부채비율 아님).

**보안**
- `.env`는 `.gitignore`에 포함되어 커밋되지 않는다. 자격증명은 data.krx.co.kr로만 전송된다.
