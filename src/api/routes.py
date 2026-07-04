from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import os
import pandas as pd
from src.collectors.krx_collector import KRXCollector
from src.collectors.yfinance_collector import YFinanceCollector
from src.storage.data_store import DataStore
from src.analyzers.financial_analyzer import FinancialAnalyzer
from src.analyzers.chart_analyzer import ChartAnalyzer
from src.collectors.news_collector import NewsCollector
from src.analyzers.news_analyzer import NewsAnalyzer
from src.analyzers.recommendation_engine import RecommendationEngine
from src.analyzers.price_target_calculator import PriceTargetCalculator

api_bp = Blueprint("api", __name__)
krx = KRXCollector()
yf = YFinanceCollector()
store = DataStore()
financial_analyzer = FinancialAnalyzer(krx, yf)
chart_analyzer = ChartAnalyzer(krx)
news_collector = NewsCollector(krx)
news_analyzer = NewsAnalyzer(news_collector)
recommendation_engine = RecommendationEngine()
price_target_calculator = PriceTargetCalculator()

DIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "dist",
)


@api_bp.route("/")
def index():
    # 빌드된 Vue3 SPA(frontend/dist/index.html) 서빙.
    # /assets/* 등 정적 자산은 Flask static_folder 설정이 자동 처리.
    return send_from_directory(DIST_DIR, "index.html")


@api_bp.route("/api/health")
def health():
    db_ok = store.ping()
    return jsonify({
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error"
    }), 200 if db_ok else 503


@api_bp.route("/api/stock/kr/<code>")
def stock_kr(code):
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        df = krx.get_ohlcv(code, start=start, end=end)
        if df.empty:
            return jsonify({"error": "No data found for code: " + code}), 404
        store.save(df, table=f"kr_{code}")
        return jsonify({
            "code": code,
            "count": len(df),
            "data": df.tail(5).to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/stock/kr/<code>/price-history")
def stock_kr_price_history(code):
    period = request.args.get("period", "1m")
    today = datetime.now()
    days_map = {"1d": 30, "1w": 91, "1m": 365, "1y": 1095}
    days = days_map.get(period, 365)
    start = (today - timedelta(days=days)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    try:
        df = krx.get_ohlcv(code, start=start, end=end)
        if df.empty:
            return jsonify({"error": "No data found for code: " + code}), 404

        df['ma5']  = df['close'].rolling(5).mean().round(0)
        df['ma20'] = df['close'].rolling(20).mean().round(0)
        df['ma60'] = df['close'].rolling(60).mean().round(0)
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = (df['ma20'] + 2 * bb_std).round(0)
        df['bb_lower'] = (df['ma20'] - 2 * bb_std).round(0)

        data = df.to_dict(orient="records")
        for row in data:
            for key in row:
                if pd.isna(row[key]):
                    row[key] = None

        return jsonify({
            "code": code,
            "period": period,
            "count": len(df),
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/stock/us/<symbol>")
def stock_us(symbol):
    period = request.args.get("period", "1mo")
    try:
        df = yf.get_ohlcv(symbol, period=period)
        store.save(df, table=f"us_{symbol.lower()}")
        return jsonify({
            "symbol": symbol,
            "count": len(df),
            "data": df.tail(5).to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _ensure_as_of(code, data):
    # 재무 데이터에 기준일이 없으면 최신 거래일(OHLCV)로 채운다.
    # 프론트는 as_of가 없으면 신뢰 불가로 보고 데이터를 숨기므로, 항상 채워준다.
    if data and not data.get("as_of"):
        try:
            df = krx.get_ohlcv(code)
            if not df.empty:
                data["as_of"] = str(df["date"].iloc[-1])[:10]
        except Exception:
            pass
    return data


@api_bp.route("/analyze/<code>/financial")
def analyze_financial(code):
    try:
        cached = store.load_financial(code)
        if cached:
            return jsonify(_ensure_as_of(code, cached))

        result = financial_analyzer.analyze(code)
        if not result:
            return jsonify({"error": "No data found for code: " + code}), 404

        result = _ensure_as_of(code, result)
        store.save_financial(code, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analyze/<code>/chart")
def analyze_chart(code):
    try:
        result = chart_analyzer.analyze(code)
        if not result:
            return jsonify({"error": "No data found for code: " + code}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analyze/<code>/news")
def analyze_news(code):
    # 실시간 수집 성공 시 캐시에 저장, 실패(빈 결과·예외) 시 캐시로 폴백한다.
    try:
        result = news_analyzer.analyze(code)
        if result:
            store.save_news(code, result)
            return jsonify(result)
        cached = store.load_news(code)
        if cached:
            cached["source"] = "cache"
            return jsonify(cached)
        return jsonify({"error": "No news found for code: " + code}), 404
    except Exception as e:
        cached = store.load_news(code)
        if cached:
            cached["source"] = "cache"
            return jsonify(cached)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analyze/<code>/recommendation")
def analyze_recommendation(code):
    # 재무·차트·뉴스 분석을 모아 정규화 후 종합 추천을 생성한다.
    # 재무/뉴스는 캐시 우선, 차트는 매번 계산. 일부 분석이 없어도 중립(0.5)으로 진행한다.
    try:
        financial = store.load_financial(code) or financial_analyzer.analyze(code)
        chart = chart_analyzer.analyze(code)
        news = store.load_news(code) or news_analyzer.analyze(code)

        if not (financial or chart or news):
            return jsonify({"error": "No data found for code: " + code}), 404

        fs = recommendation_engine.normalize_financial(financial) if financial else 0.5
        cs = recommendation_engine.normalize_chart(chart) if chart else 0.5
        ns = recommendation_engine.normalize_news(news) if news else 0.5

        result = recommendation_engine.generate(fs, cs, ns)
        result["code"] = code
        result["available"] = {
            "financial": bool(financial),
            "chart": bool(chart),
            "news": bool(news),
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analyze/<code>/price-target")
def analyze_price_target(code):
    # 현재가(PYKRX 최신 종가) 기반 목표가·손절가 제안.
    # expected_return / max_loss는 쿼리로 조절 (기본 15% / 10%).
    try:
        expected_return = float(request.args.get("expected_return", 0.15))
        max_loss = float(request.args.get("max_loss", 0.10))

        df = krx.get_ohlcv(code)
        if df.empty:
            return jsonify({"error": "No data found for code: " + code}), 404

        current_price = int(df["close"].iloc[-1])
        result = price_target_calculator.suggest(current_price, expected_return, max_loss)
        result["code"] = code
        result["as_of"] = str(df["date"].iloc[-1])[:10]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _safe(fn):
    # 부분 실패 허용: 한 분석이 실패해도 None으로 처리하고 나머지는 진행한다.
    try:
        return fn()
    except Exception:
        return None


@api_bp.route("/analyze/<code>")
def analyze_all(code):
    # Primary Seam: 재무·차트·뉴스·추천·목표가를 한 번에 통합한다.
    try:
        # 1) 종목 유효성 검증 + 현재가 (OHLCV 1회 조회로 겸용)
        df = _safe(lambda: krx.get_ohlcv(code))
        if df is None or df.empty:
            return jsonify({"error": "No data found for code: " + code}), 404

        current_price = int(df["close"].iloc[-1])
        as_of = str(df["date"].iloc[-1])[:10]

        # 2) 재무·차트·뉴스를 병렬 실행 (재무·뉴스는 캐시 우선)
        def get_financial():
            return _ensure_as_of(code, store.load_financial(code) or financial_analyzer.analyze(code))

        def get_chart():
            return chart_analyzer.analyze(code)

        def get_news():
            return store.load_news(code) or news_analyzer.analyze(code)

        with ThreadPoolExecutor(max_workers=3) as ex:
            financial = _safe(ex.submit(get_financial).result)
            chart = _safe(ex.submit(get_chart).result)
            news = _safe(ex.submit(get_news).result)

        # 라이브 결과 캐시 저장 (idempotent, 다음 호출 5초 목표에 기여)
        if financial:
            store.save_financial(code, financial)
        if news:
            store.save_news(code, news)

        # 3) 종합 추천 (없는 분석은 중립 0.5로 진행)
        fs = recommendation_engine.normalize_financial(financial) if financial else 0.5
        cs = recommendation_engine.normalize_chart(chart) if chart else 0.5
        ns = recommendation_engine.normalize_news(news) if news else 0.5
        recommendation = recommendation_engine.generate(fs, cs, ns)

        # 4) 목표가·손절 (현재가 기반)
        price_target = price_target_calculator.suggest(current_price)

        return jsonify({
            "stock_code": code,
            "stock_name": krx.get_name(code),
            "current_price": current_price,
            "as_of": as_of,
            "financial": financial,
            "chart": chart,
            "news": news,
            "recommendation": recommendation,
            "price_target": price_target,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
