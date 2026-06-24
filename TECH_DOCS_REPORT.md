# 주식 분석 시스템 - 기술 문서 조사 리포트
**작성일**: 2026-06-24  
**마감일**: 2026-07-15 (3주)  
**팀**: 3명 (Python·크롤링·AI코딩 첫 경험)

---

## 📋 목차
1. [핵심 라이브러리 가이드](#1-핵심-라이브러리-가이드)
2. [데이터 수집 스택](#2-데이터-수집-스택)
3. [분석 엔진 구축](#3-분석-엔진-구축)
4. [백엔드 API 설계](#4-백엔드-api-설계)
5. [프론트엔드 대시보드](#5-프론트엔드-대시보드)
6. [구현 로드맵](#6-구현-로드맵)
7. [주요 주의사항 & 검증 체크리스트](#7-주요-주의사항--검증-체크리스트)

---

## 1. 핵심 라이브러리 가이드

### 1.1 yfinance (해외 증시 데이터) ⭐ 필수

**목적**: Yahoo Finance API를 통해 해외 주식 시세, 재무 지표 자동 수집

#### 핵심 함수

##### `yf.download()` — 시세 데이터 다운로드
```python
import yfinance as yf

# 단일/다중 종목, 기간 지정
data = yf.download("AAPL MSFT", start="2023-01-01", end="2023-12-31")
# 반환: DataFrame with OHLCV (Open, High, Low, Close, Volume)
```

**사용 시나리오**:
- 차트 분석용 과거 시세 데이터 (일/주/월별)
- Volume, 고가/저가 등 기술적 지표 계산 기초

##### `yf.Calendars()` — 경제 일정, 실적발표, IPO 정보
```python
from datetime import datetime, timedelta

# 오늘부터 7일간 경제 이벤트 조회
calendar = yf.Calendars()

# 실적 발표 일정
earnings = calendar.get_earnings_calendar()

# IPO 정보
ipo = calendar.get_ipo_info_calendar()

# 주가 분할 공시
splits = calendar.get_splits_calendar()

# 경제 지표 발표일
econ = calendar.get_economic_events_calendar()
```

**사용 시나리오**:
- V2에서 실시간 알림용 (지금은 선택사항)
- 종목 추천 로직에 이벤트 반영 (가점 영역)

##### `yf.screen()` — 종목 스크리닝
```python
# 특정 조건의 종목 목록 조회
results = yf.screen(filters=equity_filter)
```

**사용 시나리오**:
- 저평가 종목, 고성장 기업 자동 발굴 (가점 영역)
- 현재는 수동 종목 입력으로 시작

#### ⚠️ 주의사항
- **시간대**: Yahoo Finance 데이터는 미국 EST 기준
- **가격 오류**: `repair=True` 옵션 사용 권장 (자동 보정)
  ```python
  hist = ticker.history(start="2024-01-01", repair=True)
  # 'Repaired?' 컬럼으로 수정 여부 확인 가능
  ```
- **한국 종목**: yfinance는 **KOSPI/KOSDAQ 미지원** → PYKRX 필수

---

### 1.2 PYKRX (국내 증시 데이터) ⭐ 필수

**목적**: 한국거래소(KRX) 데이터 수집 (KOSPI, KOSDAQ, ETF)

#### 설치 & 기본 사용
```bash
pip install pykrx
```

#### 핵심 함수 (예상 API, 공식 문서 참고)

**일봉 데이터**:
```python
from pykrx import stock

# 특정 기간의 일봉 데이터
df = stock.get_market_ohlcv("20230101", "20231231", "005930")  # 삼성전자
# 반환: DataFrame with Date, Open, High, Low, Close, Volume
```

**재무 정보**:
```python
# PER, PBR, EPS, ROE 등
finance = stock.get_market_fundamental("20231231", market="KOSPI")
```

**지수 데이터**:
```python
# KOSPI, KOSDAQ 지수 시계열
kospi = stock.get_index_ohlcv("20230101", "20231231", "1001")
```

**업종별 정보**:
```python
# 업종별 지수
sector = stock.get_sector_index_ohlcv("20230101", "20231231")
```

#### ⚠️ 주의사항
- **데이터 지연**: 거래일 익일 제공 (실시간 데이터 불가)
- **휴장일**: 토일/공휴일 자동 제외
- **라이센스**: 공개 데이터 (크롤링 차단 위험 없음)

---

### 1.3 pandas (데이터 분석 & 시계열 처리) ⭐⭐⭐ 핵심

**목적**: 재무 지표 계산, 시계열 데이터 처리

#### 핵심 개념: 리샘플링 (Resampling)

시계열 데이터를 다른 주기로 변환 (일봉 → 주봉/월봉)

```python
import pandas as pd

# 일봉 → 주봉 (매주 금요일 종가)
weekly = daily_df.resample('W').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
})

# 일봉 → 월봉
monthly = daily_df.resample('M').last()

# 분봉 → 5분봉
resampled_5min = intraday_df.resample('5T').sum()
```

#### 통계 함수 (Resampler)

리샘플된 데이터에 대해 다양한 통계 계산:

```python
# 기본 통계
df.resample('D').agg({
    'Close': ['mean', 'std', 'min', 'max'],
    'Volume': 'sum'
})

# OHLC 계산 (한 번에)
df['Volume'].resample('W').ohlc()

# 이동평균선 (5일, 20일, 60일)
df['MA5'] = df['Close'].rolling(window=5).mean()
df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA60'] = df['Close'].rolling(window=60).mean()

# 표준편차 (변동성 분석)
df['STD20'] = df['Close'].rolling(window=20).std()
```

#### 주의사항
- **Look-ahead Bias 방지**: `label='left'`, `closed='left'` 사용 (기본값)
- **NaN 처리**: 전체 기간 데이터 확보 후 계산 (초반 NaN 예상)

---

### 1.4 ta (기술적 지표 라이브러리) — 선택사항

**목적**: RSI, MACD, 볼린저밴드 등 자동 계산

```bash
pip install ta
```

```python
from ta.momentum import RSI, MACD
from ta.volatility import BollingerBands

# RSI (상대강도지수) - 0~100, >70 과매수, <30 과매도
rsi = RSI(close=df['Close'], window=14)
df['RSI'] = rsi.rsi()

# MACD (이동평균 수렴확산) - 추세 변화 포착
macd = MACD(close=df['Close'])
df['MACD'] = macd.macd()
df['MACD_Signal'] = macd.macd_signal()
df['MACD_Diff'] = macd.macd_diff()

# 볼린저밴드 - 변동성 분석
bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
df['BB_Upper'] = bb.bollinger_hband()
df['BB_Lower'] = bb.bollinger_lband()
```

**선택 이유**: 검증된 계산, pandas보다 간단

---

## 2. 데이터 수집 스택

### 2.1 해외 증시 (yfinance)

```
┌─ yfinance.download() ─┐
│  • 시세 데이터         │ → DataFrame
│  • 재무 지표 (PER 등)  │   (Open, High, Low, Close, Volume)
└───────────────────────┘
```

**구현 예시**:
```python
import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, start, end):
    """해외 종목 데이터 수집"""
    try:
        data = yf.download(ticker, start=start, end=end, repair=True)
        return data
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

# 사용
apple_data = fetch_stock_data("AAPL", "2024-01-01", "2024-06-30")
```

### 2.2 국내 증시 (PYKRX)

```
┌─ PYKRX ──────────────────┐
│ • stock.get_market_ohlcv │ → DataFrame (KOSPI/KOSDAQ)
│ • stock.get_sector_index │ → 업종별 정보
└──────────────────────────┘
```

**구현 예시**:
```python
from pykrx import stock
from datetime import datetime

def fetch_korean_stock(code, start_date, end_date):
    """국내 종목 데이터 수집"""
    df = stock.get_market_ohlcv(start_date, end_date, code)
    return df

# 사용 (삼성전자 KOSPI 코드: 005930)
samsung = fetch_korean_stock("005930", "20240101", "20240630")
```

### 2.3 뉴스 크롤링 (국내)

**상황**: PYKRX/yfinance는 뉴스 미지원 → **별도 크롤링 필요**

#### 옵션 1: 네이버 금융 크롤링 (권장)
```python
import requests
from bs4 import BeautifulSoup

def crawl_naver_news(keyword):
    """네이버 금융 뉴스 크롤링"""
    url = f"https://finance.naver.com/search/searchList.naver?keyword={keyword}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    news_list = []
    for item in soup.select('.tit'):  # 뉴스 제목
        title = item.get_text(strip=True)
        link = item.get('href')
        news_list.append({'title': title, 'link': link})
    
    return news_list
```

#### 옵션 2: yfinance 뉴스 (해외만)
```python
ticker = yf.Ticker("AAPL")
news = ticker.news  # 최근 뉴스 헤드라인
```

#### 주의사항
- **robots.txt 준수**: 과도한 요청 시 IP 차단
- **캐싱 필수**: 매번 크롤링 대신 로컬 저장 후 업데이트
- **에러 처리**: 연결 실패/구조 변경 대비

---

## 3. 분석 엔진 구축

### 3.1 재무 지표 계산 (기업 분석)

#### 1️⃣ 기본 지표 (수집 후 계산)

| 지표 | 계산식 | 해석 |
|------|--------|------|
| **PER** (P/E Ratio) | 주가 ÷ EPS | 저평가(낮음) vs 고평가(높음) |
| **PBR** (P/B Ratio) | 시가총액 ÷ 순자산 | BPS 대비 주가 평가 |
| **EPS** (Earnings Per Share) | 당기순이익 ÷ 발행주식수 | 주당 수익성 |
| **ROE** | 당기순이익 ÷ 자본총액 | 자본 효율성 |
| **부채비율** | 부채 ÷ 자본 | 재무 레버리지 |
| **배당수익률** | 연배당액 ÷ 주가 | 배당 수익성 |

#### 구현 예시 (pandas)
```python
import pandas as pd

class FinancialAnalyzer:
    def __init__(self, ticker_data):
        self.df = ticker_data
    
    def calculate_indicators(self, eps, net_income, equity, debt, dividend, current_price):
        """기본 재무 지표 계산"""
        indicators = {
            'PER': current_price / eps if eps > 0 else None,
            'EPS': eps,
            'ROE': (net_income / equity) * 100 if equity > 0 else None,
            'DebtRatio': debt / equity if equity > 0 else None,
            'DividendYield': (dividend / current_price) * 100 if current_price > 0 else None,
        }
        return pd.Series(indicators)
    
    def compare_with_sector(self, industry_avg):
        """동종 업계 대비 평가"""
        comparison = {
            'PER_Signal': 'Undervalued' if self.per < industry_avg['PER'] else 'Overvalued',
            'ROE_Signal': 'Strong' if self.roe > industry_avg['ROE'] else 'Weak'
        }
        return comparison
```

---

### 3.2 차트 분석 (기술적 지표)

#### 주요 지표 & 신호

**① 이동평균선 (MA)**
```python
df['MA5'] = df['Close'].rolling(5).mean()
df['MA20'] = df['Close'].rolling(20).mean()
df['MA60'] = df['Close'].rolling(60).mean()

# 신호: 골든크로스(MA5 > MA20) = 매수, 데드크로스(MA5 < MA20) = 매도
```

**② RSI (Relative Strength Index)**
```python
from ta.momentum import RSI

rsi = RSI(close=df['Close'], window=14)
df['RSI'] = rsi.rsi()

# 신호: RSI < 30 = 과매도(매수), RSI > 70 = 과매수(매도)
```

**③ MACD (Moving Average Convergence Divergence)**
```python
from ta.momentum import MACD

macd = MACD(close=df['Close'])
df['MACD'] = macd.macd()
df['Signal'] = macd.macd_signal()
df['Histogram'] = macd.macd_diff()

# 신호: MACD > Signal = 상승, MACD < Signal = 하락
```

**④ 거래량**
```python
# 거래량 증가 = 추세 강화, 거래량 감소 = 약화
df['Volume_MA20'] = df['Volume'].rolling(20).mean()
volume_signal = 'Strong' if df['Volume'].iloc[-1] > df['Volume_MA20'].iloc[-1] else 'Weak'
```

#### 신호 생성 로직
```python
class ChartAnalyzer:
    def generate_signals(self, df):
        """기술적 지표 → 매수/매도/관망 신호"""
        latest = df.iloc[-1]
        signals = []
        
        # 골든크로스 여부
        if latest['MA5'] > latest['MA20']:
            signals.append('Golden Cross')
        
        # RSI 신호
        if latest['RSI'] < 30:
            signals.append('Oversold - Buy Signal')
        elif latest['RSI'] > 70:
            signals.append('Overbought - Sell Signal')
        
        # MACD 신호
        if latest['MACD'] > latest['Signal']:
            signals.append('MACD Bullish')
        
        return signals
```

---

### 3.3 뉴스 기반 점수화 (키워드 룰)

**방식**: 감성분석(ML) 없이 **키워드 사전 기반** 점수화

```python
class NewsScorer:
    def __init__(self):
        # 긍정 키워드
        self.positive = ['호재', '상승', '실적개선', '신제품', '흑자전환', '매수추천']
        # 부정 키워드
        self.negative = ['악재', '하락', '손실확대', '리콜', '손실', '매도추천']
    
    def score_news(self, headlines):
        """뉴스 헤드라인 점수화"""
        score = 0
        
        for headline in headlines:
            # 긍정 키워드 카운트
            pos_count = sum(1 for kw in self.positive if kw in headline)
            # 부정 키워드 카운트
            neg_count = sum(1 for kw in self.negative if kw in headline)
            
            score += pos_count - neg_count
        
        return score / len(headlines) if headlines else 0
    
    def get_sentiment(self, score):
        """점수 → 감정 분류"""
        if score > 0.5:
            return 'Positive'
        elif score < -0.5:
            return 'Negative'
        else:
            return 'Neutral'
```

---

### 3.4 종목 추천 점수 합산

```python
class RecommendationEngine:
    def calculate_score(self, financial_score, chart_score, news_score):
        """최종 추천 점수 (가중평균)"""
        weights = {
            'financial': 0.4,  # 재무 40%
            'chart': 0.4,      # 기술 40%
            'news': 0.2        # 뉴스 20%
        }
        
        total = (financial_score * weights['financial'] +
                chart_score * weights['chart'] +
                news_score * weights['news'])
        
        return total
    
    def recommend(self, scores):
        """점수 → 추천 등급"""
        if scores > 0.7:
            return 'Strong Buy'
        elif scores > 0.4:
            return 'Buy'
        elif scores > -0.4:
            return 'Hold'
        elif scores > -0.7:
            return 'Sell'
        else:
            return 'Strong Sell'
```

---

### 3.5 목표가 & 손절 라인 설정

```python
class PriceTarget:
    def calculate_targets(self, current_price, expected_return, risk_tolerance):
        """목표가 & 손절 라인 자동 제안"""
        
        # 목표가 = 현재가 × (1 + 기대수익률)
        target_price = current_price * (1 + expected_return)
        
        # 손절 = 현재가 × (1 - 허용손실률)
        stop_loss = current_price * (1 - risk_tolerance)
        
        return {
            'current_price': current_price,
            'target_price': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'profit_potential': f"{(expected_return * 100):.1f}%",
            'max_loss': f"{(risk_tolerance * 100):.1f}%"
        }
    
    def example(self):
        """예시"""
        # 현재가 100,000원, 20% 수익 기대, 5% 손실 허용
        targets = self.calculate_targets(100000, 0.20, 0.05)
        # 결과:
        # target_price: 120,000원
        # stop_loss: 95,000원
```

---

## 4. 백엔드 API 설계

### 4.1 FastAPI 기본 구조

**설치**:
```bash
pip install fastapi uvicorn
```

**프로젝트 구조**:
```
backend/
├── main.py                 # FastAPI 진입점
├── api/
│   ├── analysis.py        # 분석 API
│   ├── recommendation.py   # 추천 API
│   └── report.py          # 리포트 API
├── services/
│   ├── data_collector.py   # 데이터 수집 모듈
│   ├── analyzer.py         # 분석 엔진
│   └── reporter.py         # 리포트 생성
└── models.py              # Pydantic 스키마
```

#### `main.py` — API 설정
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Stock Analysis System",
    summary="종합 주식 분석 플랫폼",
    description="재무·차트·뉴스 기반 종목 분석 및 추천",
    version="0.1.0",
)

# CORS 활성화 (프론트엔드와 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Stock Analysis API v0.1"}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

#### 분석 API 예시
```python
from fastapi import APIRouter
from pydantic import BaseModel
from services.analyzer import ChartAnalyzer, FinancialAnalyzer

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

class AnalysisRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str

class AnalysisResponse(BaseModel):
    ticker: str
    financial_score: float
    chart_signals: list
    news_sentiment: str
    recommendation: str

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(req: AnalysisRequest):
    """종목 분석 API"""
    analyzer = FinancialAnalyzer(req.ticker)
    
    result = AnalysisResponse(
        ticker=req.ticker,
        financial_score=analyzer.get_score(),
        chart_signals=analyzer.get_signals(),
        news_sentiment=analyzer.get_sentiment(),
        recommendation=analyzer.recommend()
    )
    
    return result
```

#### 추천 API 예시
```python
@router.get("/recommendations")
async def get_recommendations(market: str = "KOSPI"):
    """추천 종목 리스트"""
    from services.recommendation import RecommendationEngine
    
    engine = RecommendationEngine()
    recommendations = engine.get_top_picks(market, limit=10)
    
    return {
        "market": market,
        "timestamp": datetime.now(),
        "recommendations": recommendations
    }
```

#### 리포트 API 예시
```python
@router.get("/report/{ticker}")
async def get_report(ticker: str):
    """종목별 종합 리포트"""
    from services.reporter import ReportGenerator
    
    generator = ReportGenerator(ticker)
    report = generator.generate()
    
    return {
        "ticker": ticker,
        "date": datetime.now(),
        "report": report
    }
```

---

### 4.2 실행 방법

```bash
# 개발 서버 시작 (localhost:8000)
uvicorn main:app --reload

# 자동생성 문서 확인
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 5. 프론트엔드 대시보드

### 5.1 Vue 3 구조

**설치**:
```bash
npm install vue@3 vite
```

**프로젝트 구조**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── StockSearch.vue      # 종목 검색
│   │   ├── AnalysisCard.vue     # 분석 결과 카드
│   │   ├── ChartViewer.vue      # 차트 시각화
│   │   └── ReportViewer.vue     # 종합 리포트
│   ├── views/
│   │   ├── Dashboard.vue        # 대시보드 메인
│   │   ├── Recommendations.vue  # 추천 종목
│   │   └── Analysis.vue         # 상세 분석
│   └── App.vue
├── vite.config.js
└── package.json
```

### 5.2 핵심 컴포넌트

#### 데이터 그리드 (종목 리스트)
```vue
<template>
  <div class="table-container">
    <table v-if="filteredData.length">
      <thead>
        <tr>
          <th v-for="key in columns" 
              @click="sortBy(key)"
              :class="{ active: state.sortKey == key }">
            {{ capitalize(key) }}
            <span class="arrow" :class="state.sortOrders[key] > 0 ? 'asc' : 'dsc'">
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="entry in filteredData" :key="entry.id">
          <td v-for="key in columns">{{ entry[key] }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>검색 결과가 없습니다.</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const columns = ['종목명', 'PER', 'ROE', '신호', '추천']
const data = ref([])
const state = ref({
  sortKey: 'PER',
  sortOrders: { PER: 1, ROE: -1 }
})

const filteredData = computed(() => {
  return data.value.sort((a, b) => {
    const key = state.value.sortKey
    return (a[key] > b[key] ? 1 : -1) * state.value.sortOrders[key]
  })
})

const sortBy = (key) => {
  state.value.sortKey = key
  state.value.sortOrders[key] *= -1
}

const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1)
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
  cursor: pointer;
}

th.active {
  color: #42b983;
}

.arrow {
  display: inline-block;
  margin-left: 5px;
}

.asc::after { content: '▲'; }
.dsc::after { content: '▼'; }
</style>
```

#### 차트 시각화 (SVG 레이더 차트)
```vue
<template>
  <svg viewBox="0 0 200 200" class="polygraph">
    <g>
      <!-- 배경 그리드 -->
      <circle cx="100" cy="100" r="80" stroke="#999" fill="none"></circle>
      <circle cx="100" cy="100" r="60" stroke="#ddd" fill="none"></circle>
      <circle cx="100" cy="100" r="40" stroke="#ddd" fill="none"></circle>
      <circle cx="100" cy="100" r="20" stroke="#ddd" fill="none"></circle>
      
      <!-- 데이터 영역 -->
      <polygon :points="points" fill="#42b983" opacity="0.75"></polygon>
      
      <!-- 축 레이블 -->
      <axis-label 
        v-for="(stat, index) in stats" 
        :key="index"
        :stat="stat" 
        :index="index" 
        :total="stats.length">
      </axis-label>
    </g>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

defineProps({
  stats: {
    type: Array,
    default: () => [
      { label: '재무', value: 0.8 },
      { label: '기술', value: 0.6 },
      { label: '뉴스', value: 0.5 },
    ]
  }
})

const points = computed(() => {
  const stats = [
    { label: '재무', value: 0.8 },
    { label: '기술', value: 0.6 },
    { label: '뉴스', value: 0.5 },
  ]
  
  const angle = (Math.PI * 2) / stats.length
  
  return stats.map((stat, i) => {
    const x = 100 + stat.value * 80 * Math.cos(angle * i - Math.PI / 2)
    const y = 100 + stat.value * 80 * Math.sin(angle * i - Math.PI / 2)
    return `${x},${y}`
  }).join(' ')
})
</script>

<style scoped>
.polygraph {
  width: 300px;
  height: 300px;
  margin: 20px auto;
}
</style>
```

---

## 6. 구현 로드맵

### Week 1 (6/24~7/1) — 데이터 수집 & 지표 기초

| 담당 | 작업 | 산출물 |
|------|------|--------|
| **A** (데이터) | • yfinance/PYKRX 연동<br>• 시세 데이터 저장 (CSV/SQLite)<br>• 뉴스 크롤링 (네이버 금융) | `data_collector.py` |
| **B** (분석) | • 재무 지표 계산 (PER, PBR, ROE)<br>• 기술적 지표 (MA, RSI, MACD)<br>• 거래량 분석 | `analyzer.py` |
| **C** (대시보드) | • Vue 프로젝트 초기화<br>• API 클라이언트 설정<br>• 레이아웃 스캘레톤 | `frontend/` |

**검증**: 종목(예: AAPL, 삼성전자) 입력 → 지표 계산 확인

---

### Week 2 (7/2~7/8) — 분석 로직 & 추천 & 리포트

| 담당 | 작업 | 산출물 |
|------|------|--------|
| **A** (데이터) | • 뉴스 점수화 (키워드 룰)<br>• 데이터 정제 & 캐싱 | `news_scorer.py` |
| **B** (분석) | • 종목 추천 로직 (3개 지표 합산)<br>• 목표가/손절 라인 계산<br>• FastAPI 백엔드 기본 구조 | `recommendation.py` |
| **C** (대시보드) | • 분석 결과 카드 (AnalysisCard.vue)<br>• 종합 리포트 뷰 (ReportViewer.vue)<br>• 차트 시각화 (레이더/라인) | `components/` |

**검증**: API 호출 → 추천 등급 & 목표가 반환 확인

---

### Week 3 (7/9~7/15) — 대시보드 통합 & 발표

| 담당 | 작업 | 산출물 |
|------|------|--------|
| **A+B** (통합) | • 전체 데이터 플로우 테스트<br>• 버그 수정 & 성능 최적화<br>• 샘플 데이터 준비 | 통합 테스트 보고서 |
| **C** (완성) | • 종목 검색 (StockSearch.vue)<br>• 추천 종목 리스트 (Recommendations.vue)<br>• 대시보드 메인 (Dashboard.vue) | `frontend/` 완성 |
| **전체** | • 발표 자료 준비<br>• 라이브 시연 (3개 종목) | 프레젠테이션 |

**성공 기준**:
- ✅ 종목 입력 → 재무 + 차트 지표 표시
- ✅ 추천 리스트 출력
- ✅ 목표가·손절 자동 제안
- ✅ 종합 리포트 대시보드 표시

---

## 7. 주요 주의사항 & 검증 체크리스트

### 🚀 성공 패턴

| 항목 | 하기 | 하지 말기 |
|------|------|---------|
| **역할 분담** | 모듈별 분리 (A: 수집, B: 분석, C: UI) | 누가 뭘 하는지 불명확 |
| **테스트** | 작은 단위 테스트 (종목 1개 → 지표 확인) | 끝에 한 번에 통합 테스트 |
| **데이터** | CSV/SQLite 캐싱 + 적당한 크롤링 | 매번 실시간 요청 (차단 위험) |
| **뉴스** | 키워드 룰 (단순) | ML/감성분석 (복잡, 학습 곡선) |
| **기능 추가** | V1 5개 기능 완성 우선 | 가점 기능에 시간 소비 |

### ⚠️ 위험 신호

| 위험 | 증상 | 대응 |
|------|------|------|
| **Python 문법 막힘** | 반복문/함수 이해 안 됨 | AI 코딩 도구 적극 활용, 짧은 함수부터 |
| **뉴스 크롤링 차단** | 403/429 에러 | → 샘플 데이터 로컬 저장, 수동 입력으로 대체 |
| **git 충돌** | merge 실패 | → 매일 pull/push, 작은 PR 자주 |
| **일정 밀림** | 3일 뒤 기능 미완성 | → V1 스코프 줄이기, 가점 버림 |

### ✅ 체크리스트

#### Week 1 완료 기준
- [ ] PYKRX/yfinance에서 실제 데이터 수집 가능
- [ ] 재무 지표 5개(PER, PBR, ROE, EPS, 배당수익률) 계산 확인
- [ ] 기술적 지표 4개(MA, RSI, MACD, Volume) 계산 확인
- [ ] 뉴스 크롤링 샘플 10개 이상 수집
- [ ] FastAPI 기본 구조 & CORS 설정 완료

#### Week 2 완료 기준
- [ ] 종목 추천 로직 (3개 지표 가중합산) 구현 & 테스트
- [ ] 목표가/손절 자동 계산 (예: 100,000원 → 목표가 120,000원)
- [ ] API 엔드포인트 3개 이상 (분석, 추천, 리포트)
- [ ] Vue 대시보드 UI 스켈레톤 완성
- [ ] 차트 시각화 1개 이상 (레이더 또는 라인)

#### Week 3 완료 기준
- [ ] 전체 시스템 통합 테스트 (데이터 → 분석 → 리포트)
- [ ] 3개 종목(해외 1, 국내 2) 라이브 시연 가능
- [ ] 버그 0개 (또는 심각도 낮음)
- [ ] 발표 준비 완료

---

## 📚 참고 자료

### 공식 문서
- **yfinance**: https://github.com/ranaroussi/yfinance
- **PYKRX**: https://github.com/sharebook-kr/pykrx
- **pandas**: https://pandas.pydata.org/docs/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Vue 3**: https://vuejs.org/guide/

### 추천 학습 순서
1. **Day 1**: pandas 기초 (DataFrame, 시계열)
2. **Day 2**: yfinance 데이터 수집
3. **Day 3**: PYKRX 데이터 수집
4. **Day 4**: 지표 계산 (pandas + ta)
5. **Day 5**: FastAPI 기본 & 라우터
6. **Day 6**: Vue 컴포넌트 & API 연동
7. **Day 7+**: 통합 & 버그 수정

---

## 🎯 최종 목표

**3주 내 MVP 완성**:
- 종목 검색 입력
- 재무·차트·뉴스 점수 자동 계산
- 추천 등급 (Strong Buy ~ Strong Sell)
- 목표가·손절 라인 제안
- 종합 리포트 대시보드 표시

**V2 로드맵**: 자동매매, 실시간 알림, ML 감성분석

---

**문서 버전**: 1.0  
**최종 수정**: 2026-06-24  
**담당**: 기술 문서 조사 (context7 기반)
