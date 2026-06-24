from flask import Blueprint, jsonify, request, render_template_string
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
        .metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px; }
        .metric-box { background: #f8f9fa; padding: 12px; border-radius: 6px; }
        .metric-label { font-size: 12px; color: #7f8c8d; font-weight: 600; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; margin-top: 5px; }
        .verdict-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin-top: 10px; }
        .verdict-undervalued { background: #d4edda; color: #155724; }
        .verdict-overvalued { background: #f8d7da; color: #721c24; }
        .verdict-neutral { background: #fff3cd; color: #856404; }
        .comparison { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px; }
        .comparison-card { background: #f8f9fa; padding: 15px; border-radius: 6px; }
        .comparison-title { font-weight: 600; color: #2c3e50; margin-bottom: 10px; }
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

        <div class="card">
            <h2>💰 재무 분석 (이슈 002)</h2>
            <div id="financial-analysis" class="loading">분석 중...</div>
        </div>

        <div class="card">
            <h2>📈 기술적 분석 - 차트 분석 (이슈 003)</h2>
            <div id="chart-analysis" class="loading">분석 중...</div>
        </div>

        <div class="footer">
            <p>이슈 001: 프로젝트 초기화 & 데이터 수집 기본 구조</p>
            <p>이슈 002: 삼성전자 재무 분석 엔드포인트 구현</p>
            <p>이슈 003: 삼성전자 기술적 분석 차트 API 구현</p>
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

        // 재무 분석 데이터 조회
        fetch('/analyze/005930/financial')
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('financial-analysis').innerHTML = '<span class="error">오류: ' + data.error + '</span>';
                    return;
                }

                const verdictClass = 'verdict-' + (
                    data.verdict === '저평가' ? 'undervalued' :
                    data.verdict === '고평가' ? 'overvalued' : 'neutral'
                );

                const perStatus = data.per < data.industry_avg.per ? '✓ 저평가' : '✗ 고평가';
                const pbrStatus = data.pbr < data.industry_avg.pbr ? '✓ 저평가' : '✗ 고평가';

                document.getElementById('financial-analysis').innerHTML = `
                    <div style="margin-top: 15px;">
                        <div style="margin-bottom: 20px;">
                            <strong style="font-size: 18px;">판정 결과</strong>
                            <div class="verdict-badge ${verdictClass}" style="font-size: 16px;">
                                ${data.verdict}
                            </div>
                        </div>

                        <div class="metrics-grid">
                            <div class="metric-box">
                                <div class="metric-label">PER (주가수익비율)</div>
                                <div class="metric-value">${data.per.toFixed(1)}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    업계평균: ${data.industry_avg.per.toFixed(1)} ${perStatus}
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">PBR (주가순자산비율)</div>
                                <div class="metric-value">${data.pbr.toFixed(2)}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    업계평균: ${data.industry_avg.pbr.toFixed(2)} ${pbrStatus}
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">ROE (자기자본수익률)</div>
                                <div class="metric-value">${data.roe.toFixed(1)}%</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    업계평균: ${data.industry_avg.roe.toFixed(1)}%
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">배당수익률</div>
                                <div class="metric-value">${data.dividend_yield.toFixed(2)}%</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    업계평균: ${data.industry_avg.dividend_yield.toFixed(2)}%
                                </div>
                            </div>
                        </div>

                        <div class="comparison">
                            <div class="comparison-card">
                                <div class="comparison-title">📊 삼성전자 재무지표</div>
                                <div style="font-size: 12px; line-height: 1.8; color: #495057;">
                                    <div>EPS: ${data.eps.toLocaleString()}원</div>
                                    <div>BPS: ${data.bps.toLocaleString()}원</div>
                                    <div>부채비율: ${data.debt_ratio.toFixed(1)}%</div>
                                </div>
                            </div>
                            <div class="comparison-card">
                                <div class="comparison-title">🏭 반도체 업계 평균</div>
                                <div style="font-size: 12px; color: #7f8c8d;">
                                    <div>4개사 (SK하이닉스, DB하이텍, 주성엔지니어링, 원익IPS)</div>
                                    <div style="margin-top: 8px; color: #495057;">
                                        PER: ${data.industry_avg.per.toFixed(1)} | PBR: ${data.industry_avg.pbr.toFixed(2)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            })
            .catch(e => {
                document.getElementById('financial-analysis').innerHTML = '<span class="error">재무 분석 로드 실패: ' + e.message + '</span>';
            });

        // 차트 분석 데이터 조회
        fetch('/analyze/005930/chart')
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('chart-analysis').innerHTML = '<span class="error">오류: ' + data.error + '</span>';
                    return;
                }

                const signalClass = data.signal === 'buy' ? 'value-up' : (data.signal === 'sell' ? 'value-down' : 'neutral');
                const signalColor = data.signal === 'buy' ? '#27ae60' : (data.signal === 'sell' ? '#e74c3c' : '#f39c12');
                const signalKo = data.signal === 'buy' ? '매수' : (data.signal === 'sell' ? '매도' : '중립');

                document.getElementById('chart-analysis').innerHTML = `
                    <div style="margin-top: 15px;">
                        <div style="margin-bottom: 20px;">
                            <strong style="font-size: 18px;">매매 신호</strong>
                            <div style="display: inline-block; background: ${signalColor}; color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; margin-top: 10px; font-size: 16px;">
                                ${signalKo} (신뢰도: ${(data.confidence * 100).toFixed(0)}%)
                            </div>
                        </div>

                        <div class="metrics-grid">
                            <div class="metric-box">
                                <div class="metric-label">RSI (14주기)</div>
                                <div class="metric-value">${data.rsi.toFixed(2)}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    ${data.rsi < 30 ? '과매도' : (data.rsi > 70 ? '과매수' : '중립')}
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">이동평균선 20일</div>
                                <div class="metric-value">${data.ma_20.toLocaleString()}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    ${data.ma_20 > data.ma_50 ? '↑ 상승추세' : '↓ 하락추세'}
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">이동평균선 50일</div>
                                <div class="metric-value">${data.ma_50.toLocaleString()}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    기준선
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">MACD 히스토그램</div>
                                <div class="metric-value" style="color: ${data.macd.histogram > 0 ? '#27ae60' : '#e74c3c'}">
                                    ${data.macd.histogram.toFixed(2)}
                                </div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    ${data.macd.histogram > 0 ? '상승' : '하락'}
                                </div>
                            </div>
                        </div>

                        <div class="comparison">
                            <div class="comparison-card">
                                <div class="comparison-title">📊 기술적 지표</div>
                                <div style="font-size: 12px; line-height: 1.8; color: #495057;">
                                    <div>MACD Line: ${data.macd.line.toFixed(2)}</div>
                                    <div>MACD Signal: ${data.macd.signal.toFixed(2)}</div>
                                    <div>MACD Histogram: ${data.macd.histogram.toFixed(2)}</div>
                                </div>
                            </div>
                            <div class="comparison-card">
                                <div class="comparison-title">📈 볼린저밴드 (20, 2σ)</div>
                                <div style="font-size: 12px; line-height: 1.8; color: #495057;">
                                    <div>상단: ${data.bollinger_band.upper.toLocaleString()}</div>
                                    <div>중단: ${data.bollinger_band.middle.toLocaleString()}</div>
                                    <div>하단: ${data.bollinger_band.lower.toLocaleString()}</div>
                                </div>
                            </div>
                        </div>

                        <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px; font-size: 12px; color: #495057; line-height: 1.6;">
                            <strong>신호 판단 규칙:</strong><br>
                            • <span style="color: #27ae60;">매수:</span> RSI < 30 AND 20일선 > 50일선<br>
                            • <span style="color: #e74c3c;">매도:</span> RSI > 70 AND 20일선 < 50일선<br>
                            • <span style="color: #f39c12;">중립:</span> 위 조건 이외
                        </div>
                    </div>
                `;
            })
            .catch(e => {
                document.getElementById('chart-analysis').innerHTML = '<span class="error">차트 분석 로드 실패: ' + e.message + '</span>';
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


@api_bp.route("/analyze/<code>/chart")
def analyze_chart(code):
    try:
        result = chart_analyzer.analyze(code)
        if not result:
            return jsonify({"error": "No data found for code: " + code}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
