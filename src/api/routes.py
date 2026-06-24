from flask import Blueprint, jsonify, request, render_template_string
from src.collectors.krx_collector import KRXCollector
from src.collectors.yfinance_collector import YFinanceCollector
from src.storage.data_store import DataStore
from src.analyzers.financial_analyzer import FinancialAnalyzer

api_bp = Blueprint("api", __name__)
krx = KRXCollector()
yf = YFinanceCollector()
store = DataStore()
financial_analyzer = FinancialAnalyzer(krx, yf)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>주식 분석 시스템</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: #2c3e50; color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        header h1 { font-size: 32px; margin-bottom: 10px; }
        header p { font-size: 16px; opacity: 0.9; }
        .status { display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }
        .status-item { display: flex; align-items: center; gap: 8px; }
        .status-badge { background: #27ae60; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .main { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card h2 { color: #2c3e50; margin-bottom: 15px; font-size: 20px; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .data-table th { background: #f8f9fa; padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6; font-weight: 600; color: #495057; }
        .data-table td { padding: 12px; border-bottom: 1px solid #dee2e6; }
        .data-table tr:hover { background: #f8f9fa; }
        .status-ok { color: #27ae60; font-weight: bold; }
        .status-error { color: #e74c3c; font-weight: bold; }
        .value-up { color: #27ae60; }
        .value-down { color: #e74c3c; }
        .chart-container { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 15px; text-align: center; color: #7f8c8d; }
        .footer { text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }
        .loading { color: #7f8c8d; font-size: 14px; }
        .error { color: #e74c3c; background: #fadbd8; padding: 12px; border-radius: 4px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📈 주식 분석 시스템 v1.0</h1>
            <p>PYKRX와 yfinance를 기반으로 한 다중 종목 분석 플랫폼</p>
            <div class="status">
                <div class="status-item">
                    <span class="status-badge" id="db-status">데이터베이스</span>
                    <span id="db-text">연결 중...</span>
                </div>
                <div class="status-item">
                    <span class="status-badge">API Server</span>
                    <span id="api-text">http://localhost:5000</span>
                </div>
            </div>
        </header>

        <div class="main">
            <div class="card">
                <h2>🇰🇷 국내 주식 데이터 (PYKRX)</h2>
                <p>삼성전자 (005930)</p>
                <div id="krx-data" class="loading">데이터 로드 중...</div>
            </div>

            <div class="card">
                <h2>💾 데이터베이스 상태</h2>
                <div id="db-info" class="loading">확인 중...</div>
            </div>
        </div>

        <div class="card">
            <h2>📊 최근 시세 데이터</h2>
            <table class="data-table" id="data-table-container">
                <thead>
                    <tr>
                        <th>날짜</th>
                        <th>시가</th>
                        <th>고가</th>
                        <th>저가</th>
                        <th>종가</th>
                        <th>거래량</th>
                    </tr>
                </thead>
                <tbody id="data-rows">
                    <tr><td colspan="6" class="loading">데이터 로드 중...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>이슈 001: 프로젝트 초기화 & 데이터 수집 기본 구조</p>
            <p>© 2026 주식 분석 시스템 | Flask + PYKRX + yfinance</p>
        </div>
    </div>

    <script>
        // DB 상태 확인
        fetch('/health')
            .then(r => r.json())
            .then(data => {
                const statusElement = document.getElementById('db-text');
                const dbInfo = document.getElementById('db-info');
                if (data.status === 'ok') {
                    statusElement.textContent = '✓ 정상 연결';
                    statusElement.style.color = '#27ae60';
                    dbInfo.innerHTML = '<span class="status-ok">✓ SQLite 데이터베이스 연결됨</span><p style="margin-top: 10px; color: #7f8c8d;">경로: data/stock_data.db</p>';
                } else {
                    statusElement.textContent = '✗ 연결 실패';
                    statusElement.style.color = '#e74c3c';
                    dbInfo.innerHTML = '<span class="status-error">✗ 데이터베이스 연결 실패</span>';
                }
            })
            .catch(e => {
                document.getElementById('db-text').textContent = '✗ 오류';
                document.getElementById('db-info').innerHTML = '<span class="status-error">✗ 오류: ' + e.message + '</span>';
            });

        // PYKRX 데이터 조회
        fetch('/api/stock/kr/005930')
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('krx-data').innerHTML = '<span class="error">오류: ' + data.error + '</span>';
                    return;
                }
                const latest = data.data[data.data.length - 1];
                const change = parseFloat(latest.change);
                const changeClass = change > 0 ? 'value-up' : 'value-down';
                const changeText = (change > 0 ? '+' : '') + change.toFixed(2) + '%';

                document.getElementById('krx-data').innerHTML = `
                    <div style="display: grid; gap: 12px; margin-top: 15px;">
                        <div><strong>종목명:</strong> 삼성전자</div>
                        <div><strong>코드:</strong> 005930</div>
                        <div><strong>현재가:</strong> <span style="font-size: 24px; font-weight: bold;">${latest.close.toLocaleString()}</span> ₩</div>
                        <div><strong>변화율:</strong> <span class="${changeClass}" style="font-size: 18px;">${changeText}</span></div>
                        <div><strong>거래량:</strong> ${(latest.volume / 1000000).toFixed(1)}M</div>
                        <div><strong>조회:</strong> ${data.count}개 날짜 데이터</div>
                    </div>
                `;

                // 데이터 테이블 업데이트
                const tbody = document.getElementById('data-rows');
                tbody.innerHTML = '';
                data.data.slice().reverse().slice(0, 10).forEach(row => {
                    const changePercent = parseFloat(row.change);
                    const changeClass = changePercent > 0 ? 'value-up' : 'value-down';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.date}</td>
                        <td>${row.open.toLocaleString()}</td>
                        <td>${row.high.toLocaleString()}</td>
                        <td>${row.low.toLocaleString()}</td>
                        <td><strong>${row.close.toLocaleString()}</strong></td>
                        <td class="${changeClass}">${(row.volume / 1000000).toFixed(1)}M</td>
                    `;
                    tbody.appendChild(tr);
                });
            })
            .catch(e => {
                document.getElementById('krx-data').innerHTML = '<span class="error">오류: ' + e.message + '</span>';
                document.getElementById('data-rows').innerHTML = '<tr><td colspan="6" class="error">데이터 로드 실패</td></tr>';
            });
    </script>
</body>
</html>
"""


@api_bp.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


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
        result = financial_analyzer.analyze(code)
        if not result:
            return jsonify({"error": "No data found for code: " + code}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
