from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import os
import time
import pandas as pd
from src.collectors.krx_collector import KRXCollector
from src.collectors.index_collector import IndexCollector
from src.storage.data_store import DataStore
from src.analyzers.financial_analyzer import FinancialAnalyzer
from src.analyzers.chart_analyzer import ChartAnalyzer
from src.collectors.news_collector import NewsCollector
from src.analyzers.news_analyzer import NewsAnalyzer
from src.analyzers.recommendation_engine import RecommendationEngine
from src.analyzers.price_target_calculator import PriceTargetCalculator

api_bp = Blueprint("api", __name__)
krx = KRXCollector()
store = DataStore()
financial_analyzer = FinancialAnalyzer(krx)
chart_analyzer = ChartAnalyzer(krx)
news_collector = NewsCollector(krx)
news_analyzer = NewsAnalyzer(news_collector)
recommendation_engine = RecommendationEngine()
price_target_calculator = PriceTargetCalculator()
index_collector = IndexCollector()

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


@api_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    return jsonify(krx.search(q) if q else [])


@api_bp.route("/api/indices")
def indices():
    # 홈 화면용 주요 지수(코스피·코스닥·나스닥·S&P500·다우) 가격·등락률
    return jsonify(index_collector.get_indices())


_top_volume_cache = {}  # (market, limit) -> {"ts", "data"}
_TOP_VOLUME_TTL = 300    # 5분 캐시(차트 분석이 무거워 재조회 방지)


@api_bp.route("/api/top-volume")
def top_volume():
    # 거래량 상위 종목 + 기술적 평가(5단계). 홈 사이드바 '거래량 상위' 화면용.
    # 추천 등급은 chart_analyzer 지표 투표 점수를 TradingView식 5단계로 매핑한다.
    market = request.args.get("market", "KOSPI").upper()
    try:
        limit = min(int(request.args.get("limit", 100)), 100)
    except ValueError:
        limit = 100

    key = (market, limit)
    cached = _top_volume_cache.get(key)
    if cached and time.time() - cached["ts"] < _TOP_VOLUME_TTL:
        return jsonify(cached["data"])

    try:
        ranking = krx.get_top_volume(market, limit)
        if not ranking:
            return jsonify({"error": "거래량 상위 종목을 가져오지 못했습니다."}), 502

        def analyze_one(item):
            chart = _safe(lambda: chart_analyzer.analyze(item["code"]))
            score = (chart or {}).get("score")
            rating = recommendation_engine.technical_rating(score)
            return {
                **item,
                "score": score,
                "signal": (chart or {}).get("signal"),
                "rating": rating["grade"],
                "rating_label": rating["label"],
            }

        # 종목별 차트 분석은 독립적이라 병렬 실행(순서는 거래량 순위 유지)
        with ThreadPoolExecutor(max_workers=12) as ex:
            stocks = list(ex.map(analyze_one, ranking))

        for i, s in enumerate(stocks, start=1):
            s["rank"] = i

        result = {"market": market, "count": len(stocks), "stocks": stocks}
        _top_volume_cache[key] = {"ts": time.time(), "data": result}
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/quote/<code>")
def quote(code):
    # 관심 종목 목록용 경량 시세(현재가·등락률)
    q = krx.get_quote(code)
    if not q:
        return jsonify({"error": "No quote for code: " + code}), 404
    return jsonify(q)


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
    period = request.args.get("period", "all")
    interval = request.args.get("interval", "day")
    today = datetime.now()
    # all = 전체 히스토리(pykrx 최대 약 3000거래일). 나머지는 lookback 일수.
    days_map = {"1d": 30, "1w": 91, "1m": 365, "1y": 1095, "all": 8000}
    days = days_map.get(period, 8000)
    start = (today - timedelta(days=days)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    try:
        df = krx.get_ohlcv(code, start=start, end=end)
        if df.empty:
            return jsonify({"error": "No data found for code: " + code}), 404

        # 캔들 간격 리샘플링: 주간/월별/연도별은 기간 내 종가(마지막)를 대표값으로.
        rule = {"week": "W", "month": "ME", "year": "YE"}.get(interval)
        if rule:
            idx = pd.to_datetime(df["date"])
            agg = df.set_index(idx).resample(rule).agg(
                {"open": "first", "high": "max", "low": "min",
                 "close": "last", "volume": "sum"}
            ).dropna(subset=["close"])
            agg["date"] = agg.index.strftime("%Y-%m-%d")
            df = agg.reset_index(drop=True)

        # 이동평균·볼린저밴드는 (리샘플된) 캔들 기준으로 계산
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
            "interval": interval,
            "count": len(df),
            "data": data
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


@api_bp.route("/analyze/<code>/overview")
def analyze_overview(code):
    # 개요 탭용. 여러 소스를 묶어 반환. 실패한 필드는 null 폴백.
    try:
        df = krx.get_ohlcv(code)
        if df is None or df.empty:
            return jsonify({"error": "No data found for code: " + code}), 404

        current_price = int(df["close"].iloc[-1])
        as_of = str(df["date"].iloc[-1])[:10]
        volume = int(df["volume"].iloc[-1])

        # 등락: 최근 2봉 종가 차이 (없으면 change 컬럼)
        change = change_rate = None
        try:
            if len(df) >= 2:
                prev = float(df["close"].iloc[-2])
                change = round(current_price - prev)
                change_rate = round((current_price - prev) / prev * 100, 2) if prev else None
        except Exception:
            pass

        # 52주 최고/최저: pykrx 1년 OHLCV로 계산. 실패 시 null.
        week52_high = week52_low = None
        try:
            today = datetime.now()
            start = (today - timedelta(days=365)).strftime("%Y%m%d")
            end = today.strftime("%Y%m%d")
            ydf = krx.get_ohlcv(code, start=start, end=end)
            if ydf is not None and not ydf.empty:
                week52_high = int(ydf["high"].max())
                week52_low = int(ydf["low"].min())
        except Exception:
            pass

        # sector: 재무 분석의 업종명(industry_name)
        fin = _safe(lambda: store.load_financial(code) or financial_analyzer.analyze(code))
        sector = (fin or {}).get("industry_name")

        foreign_ratio = _safe(lambda: krx.get_foreign_ratio(code))

        return jsonify({
            "code": code,
            "name": krx.get_name(code),
            "as_of": as_of,
            "current_price": current_price,
            "change": change,
            "change_rate": change_rate,
            "market_cap": _safe(lambda: krx.get_market_cap_value(code)),
            "sector": sector,
            "summary": _safe(lambda: krx.get_company_summary(code)),
            "week52_high": week52_high,
            "week52_low": week52_low,
            "volume": volume,
            "foreign_ratio": foreign_ratio,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analyze/<code>/financial")
def analyze_financial(code):
    try:
        cached = store.load_financial(code)
        result = cached if cached else financial_analyzer.analyze(code)
        if not result:
            return jsonify({"error": "No data found for code: " + code}), 404

        result = _ensure_as_of(code, result)
        if not cached:
            store.save_financial(code, result)

        # 확장(하위호환): 연간 실적·유보율. 실패해도 기존 응답 유지.
        result = _extend_financial(code, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _extend_financial(code, result):
    # 네이버 '기업실적분석'에서 연간 실적·유보율·부채비율을 수집.
    # 절대 지어내지 않고, 못 구하면 빈 배열/None 유지.
    nf = _safe(lambda: krx.get_naver_financials(code)) or {}

    result["annual"] = nf.get("annual") or []
    result["retention_ratio"] = nf.get("retention_ratio")

    # 부채비율: 기존 값이 없거나 0이면 네이버 값으로 보완.
    if nf.get("debt_ratio") is not None and not result.get("debt_ratio"):
        result["debt_ratio"] = nf["debt_ratio"]
    return result


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

        # 확장(하위호환): confidence·factors·dimensions + 목표가/손절/현재가.
        try:
            result = recommendation_engine.extend(result, financial, chart, news, fs, cs, ns)
        except Exception:
            pass
        try:
            df = krx.get_ohlcv(code)
            if df is not None and not df.empty:
                current_price = int(df["close"].iloc[-1])
                pt = price_target_calculator.suggest(current_price)
                result["current_price"] = current_price
                result["target_price"] = pt.get("target_price")
                result["stop_loss"] = pt.get("stop_loss")
        except Exception:
            pass
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

        # 확장(하위호환): upside·피벗 지지/저항·시나리오. 실패해도 기존 응답 유지.
        try:
            last = df.iloc[-1]
            result = price_target_calculator.extend(
                result,
                high=float(last["high"]),
                low=float(last["low"]),
                close=float(last["close"]),
            )
        except Exception:
            price_target_calculator.extend(result)
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
