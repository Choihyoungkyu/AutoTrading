from flask import Blueprint, jsonify, request
from src.collectors.krx_collector import KRXCollector
from src.collectors.yfinance_collector import YFinanceCollector
from src.storage.data_store import DataStore

api_bp = Blueprint("api", __name__)
krx = KRXCollector()
yf = YFinanceCollector()
store = DataStore()


@api_bp.route("/")
def index():
    return jsonify({
        "service": "주식 분석 시스템",
        "version": "1.0.0",
        "status": "running"
    })


@api_bp.route("/health")
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
