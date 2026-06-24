from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime, timedelta
import os
import pandas as pd
from src.collectors.krx_collector import KRXCollector
from src.collectors.yfinance_collector import YFinanceCollector
from src.storage.data_store import DataStore
from src.analyzers.financial_analyzer import FinancialAnalyzer
from src.analyzers.chart_analyzer import ChartAnalyzer

api_bp = Blueprint("api", __name__)
krx = KRXCollector()
yf = YFinanceCollector()
store = DataStore()
financial_analyzer = FinancialAnalyzer(krx, yf)
chart_analyzer = ChartAnalyzer(yf)

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


@api_bp.route("/analyze/<code>/financial")
def analyze_financial(code):
    try:
        cached = store.load_financial(code)
        if cached:
            return jsonify(cached)

        result = financial_analyzer.analyze(code)
        if not result:
            return jsonify({"error": "No data found for code: " + code}), 404

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
