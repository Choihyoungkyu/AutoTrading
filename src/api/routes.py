from flask import Blueprint, jsonify, request, render_template_string
from datetime import datetime, timedelta
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>주식 분석 시스템</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 15px; }
        header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        header h1 { font-size: 24px; margin-bottom: 8px; }
        header p { font-size: 14px; opacity: 0.9; }
        .status { display: flex; gap: 12px; margin-top: 15px; flex-wrap: wrap; }
        .status-item { display: flex; align-items: center; gap: 6px; font-size: 12px; }
        .status-badge { background: #27ae60; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .main { display: grid; grid-template-columns: 1fr; gap: 15px; margin-bottom: 20px; }
        .card { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card h2 { color: #2c3e50; margin-bottom: 12px; font-size: 18px; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
        .data-table th { background: #f8f9fa; padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6; font-weight: 600; color: #495057; font-size: 12px; }
        .data-table td { padding: 8px; border-bottom: 1px solid #dee2e6; }
        .data-table tr:hover { background: #f8f9fa; }
        .status-ok { color: #27ae60; font-weight: bold; }
        .status-error { color: #e74c3c; font-weight: bold; }
        .value-up { color: #27ae60; }
        .value-down { color: #e74c3c; }
        .footer { text-align: center; color: #7f8c8d; font-size: 11px; margin-top: 20px; }
        .loading { color: #7f8c8d; font-size: 13px; }
        .error { color: #e74c3c; background: #fadbd8; padding: 10px; border-radius: 4px; margin-top: 12px; font-size: 12px; }
        .metrics-grid { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 12px; }
        .metric-box { background: #f8f9fa; padding: 10px; border-radius: 6px; }
        .metric-label { font-size: 11px; color: #7f8c8d; font-weight: 600; }
        .metric-value { font-size: 20px; font-weight: bold; color: #2c3e50; margin-top: 4px; }
        .verdict-badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-weight: bold; margin-top: 8px; font-size: 14px; }
        .verdict-undervalued { background: #d4edda; color: #155724; }
        .verdict-overvalued { background: #f8d7da; color: #721c24; }
        .verdict-neutral { background: #fff3cd; color: #856404; }
        .comparison { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 12px; }
        .comparison-card { background: #f8f9fa; padding: 12px; border-radius: 6px; }
        .comparison-title { font-weight: 600; color: #2c3e50; margin-bottom: 8px; font-size: 14px; }
        .tooltip-icon { display: inline-block; width: 14px; height: 14px; margin-left: 4px; background: #3498db; color: white; border-radius: 50%; text-align: center; line-height: 14px; font-size: 9px; font-weight: bold; cursor: help; position: relative; }
        .tooltip-icon:hover::after { content: attr(data-tooltip); position: absolute; background: #2c3e50; color: white; padding: 6px 10px; border-radius: 4px; font-size: 11px; bottom: 120%; left: 50%; transform: translateX(-50%); z-index: 999; box-shadow: 0 2px 8px rgba(0,0,0,0.2); font-weight: normal; white-space: pre-wrap; word-wrap: break-word; width: 200px; text-align: center; }
        .tooltip-icon:hover::before { content: ""; position: absolute; background: #2c3e50; width: 4px; height: 4px; bottom: 110%; left: 50%; transform: translateX(-50%) rotate(45deg); z-index: 999; }
        .ind-btn { position: relative; }
        .ind-btn:hover::after { content: attr(data-tooltip); position: absolute; background: #2c3e50; color: white; padding: 8px 12px; border-radius: 4px; font-size: 11px; width: 240px; bottom: 130%; left: 50%; transform: translateX(-50%); z-index: 999; box-shadow: 0 2px 8px rgba(0,0,0,0.2); line-height: 1.5; text-align: center; white-space: pre-wrap; word-wrap: break-word; display: block; }
        .ind-btn:hover::before { content: ""; position: absolute; background: #2c3e50; width: 4px; height: 4px; bottom: 120%; left: 50%; transform: translateX(-50%) rotate(45deg); z-index: 999; }
        .period-buttons { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
        .period-btn { padding: 5px 14px; border: 1px solid #dee2e6; border-radius: 20px; background: white; cursor: pointer; font-size: 12px; color: #495057; transition: all 0.15s; }
        .period-btn:hover { background: #e9ecef; }
        .period-btn.active { background: #2c3e50; color: white; border-color: #2c3e50; }
        .indicator-filters { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
        .ind-btn { padding: 4px 12px; border-radius: 20px; border: 2px solid; background: white; cursor: pointer; font-size: 11px; font-weight: 600; transition: all 0.15s; }
        .ind-btn.active { color: white !important; }
        .price-chart-wrap { position: relative; height: 250px; margin-top: 8px; }

        /* Tablet (768px 이상) */
        @media (min-width: 768px) {
            .container { padding: 20px; }
            header { padding: 30px; margin-bottom: 30px; }
            header h1 { font-size: 28px; }
            header p { font-size: 15px; }
            .status { gap: 20px; margin-top: 20px; }
            .status-item { gap: 8px; font-size: 13px; }
            .status-badge { padding: 6px 12px; font-size: 12px; }
            .main { grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
            .card { padding: 20px; margin-bottom: 20px; }
            .card h2 { font-size: 20px; margin-bottom: 15px; }
            .data-table { font-size: 14px; margin-top: 15px; }
            .data-table th { padding: 12px; font-size: 13px; }
            .data-table td { padding: 12px; }
            .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .metric-box { padding: 12px; }
            .metric-label { font-size: 12px; }
            .metric-value { font-size: 24px; }
            .verdict-badge { padding: 8px 16px; font-size: 16px; }
            .comparison { grid-template-columns: 1fr 1fr; gap: 20px; }
            .comparison-card { padding: 15px; }
            .comparison-title { font-size: 15px; }
            .footer { font-size: 13px; margin-top: 30px; }
            .loading { font-size: 14px; }
            .error { padding: 12px; font-size: 13px; }
            .period-buttons { gap: 8px; }
            .period-btn { padding: 6px 18px; font-size: 14px; }
            .indicator-filters { gap: 8px; margin-bottom: 12px; }
            .ind-btn { padding: 4px 14px; font-size: 12px; }
            .price-chart-wrap { height: 320px; }
            .tooltip-icon { width: 16px; height: 16px; line-height: 16px; font-size: 11px; }
            .tooltip-icon:hover::after { font-size: 12px; width: 250px; }
            .ind-btn:hover::after { font-size: 13px; width: 320px; }
        }

        /* Desktop (1024px 이상) */
        @media (min-width: 1024px) {
            .container { padding: 20px; }
            .price-chart-wrap { height: 380px; }
        }

        /* 테이블 모바일 스크롤 */
        .data-table { overflow-x: auto; display: block; }
        @media (max-width: 767px) {
            .data-table { font-size: 12px; }
            .data-table th { padding: 6px; font-size: 11px; }
            .data-table td { padding: 6px; }
            .data-table th:nth-child(2),
            .data-table th:nth-child(3),
            .data-table th:nth-child(4),
            .data-table td:nth-child(2),
            .data-table td:nth-child(3),
            .data-table td:nth-child(4) { font-size: 11px; }
        }
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
            <h2>📉 주가 차트 (삼성전자 005930)</h2>
            <div class="period-buttons">
                <button class="period-btn" data-period="1d" onclick="loadPriceChart('1d')">일</button>
                <button class="period-btn" data-period="1w" onclick="loadPriceChart('1w')">주</button>
                <button class="period-btn active" data-period="1m" onclick="loadPriceChart('1m')">달</button>
                <button class="period-btn" data-period="1y" onclick="loadPriceChart('1y')">년</button>
            </div>
            <div class="indicator-filters">
                <button class="ind-btn" id="ind-ma5" style="border-color:#e74c3c;color:#e74c3c" data-tooltip="최근 5일 평균가격. 가장 빠른 단기 추세 변화를 나타냄" onclick="toggleIndicator('ma5')">MA5</button>
                <button class="ind-btn active" id="ind-ma20" style="border-color:#f39c12;background:#f39c12;color:#f39c12" data-tooltip="최근 20일 평균가격. 단기 추세와 매매신호를 나타냄" onclick="toggleIndicator('ma20')">MA20</button>
                <button class="ind-btn" id="ind-ma60" style="border-color:#2980b9;color:#2980b9" data-tooltip="최근 60일 평균가격. 중기 추세의 흐름을 나타냄" onclick="toggleIndicator('ma60')">MA60</button>
                <button class="ind-btn" id="ind-bb" style="border-color:#9b59b6;color:#9b59b6" data-tooltip="이동평균을 중심으로 표준편차 범위의 밴드. 가격 변동성과 과매수/과매도를 나타냄" onclick="toggleIndicator('bb')">볼린저밴드</button>
            </div>
            <div id="price-chart-asof" style="font-size:12px;color:#7f8c8d;margin-top:8px;"></div>
            <div class="price-chart-wrap">
                <canvas id="priceChart"></canvas>
            </div>
            <div id="price-chart-error"></div>
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
        // 주가 차트
        let priceChartInstance = null;
        let priceChartData = null;
        const activeIndicators = new Set(['ma20']);

        function toggleIndicator(ind) {
            const btn = document.getElementById('ind-' + ind);
            const colorMap = { ma5: '#e74c3c', ma20: '#f39c12', ma60: '#2980b9', bb: '#9b59b6' };
            const borderColor = btn.style.borderColor;

            if (activeIndicators.has(ind)) {
                activeIndicators.delete(ind);
                btn.classList.remove('active');
                btn.style.background = 'white';
                btn.style.color = borderColor;  // 테두리색과 동일하게 설정
            } else {
                activeIndicators.add(ind);
                btn.classList.add('active');
                btn.style.background = colorMap[ind];
                btn.style.color = 'white';  // 선택 시 흰색
            }
            if (priceChartData) {
                renderPriceChart(priceChartData);
            }
        }

        function renderPriceChart(data) {
            const labels = data.data.map(d => d.date);
            const closes = data.data.map(d => d.close);

            const asofEl = document.getElementById('price-chart-asof');
            if (asofEl) asofEl.textContent = data.data.length ? ('기준일: ' + data.data[data.data.length - 1].date) : '';

            const datasets = [{
                label: '종가',
                data: closes,
                borderColor: '#2c3e50',
                backgroundColor: (() => {
                    const ctx = document.getElementById('priceChart').getContext('2d');
                    const gradient = ctx.createLinearGradient(0, 0, 0, 320);
                    gradient.addColorStop(0, 'rgba(44,62,80,0.25)');
                    gradient.addColorStop(1, 'rgba(44,62,80,0)');
                    return gradient;
                })(),
                borderWidth: 2,
                pointRadius: labels.length > 60 ? 0 : 2,
                fill: true,
                tension: 0.1
            }];

            if (activeIndicators.has('ma5')) {
                datasets.push({
                    label: 'MA5',
                    data: data.data.map(d => d.ma5),
                    borderColor: '#e74c3c',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1
                });
            }
            if (activeIndicators.has('ma20')) {
                datasets.push({
                    label: 'MA20',
                    data: data.data.map(d => d.ma20),
                    borderColor: '#f39c12',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1
                });
            }
            if (activeIndicators.has('ma60')) {
                datasets.push({
                    label: 'MA60',
                    data: data.data.map(d => d.ma60),
                    borderColor: '#2980b9',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1
                });
            }
            if (activeIndicators.has('bb')) {
                datasets.push({
                    label: 'BB Upper',
                    data: data.data.map(d => d.bb_upper),
                    borderColor: '#9b59b6',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1
                });
                datasets.push({
                    label: 'BB Lower',
                    data: data.data.map(d => d.bb_lower),
                    borderColor: '#9b59b6',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: '-1',
                    backgroundColor: 'rgba(155,89,182,0.1)',
                    tension: 0.1
                });
            }

            if (priceChartInstance) priceChartInstance.destroy();

            const ctx = document.getElementById('priceChart').getContext('2d');
            priceChartInstance = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: true },
                        tooltip: {
                            callbacks: {
                                label: ctx => ctx.dataset.label + ': ₩' + (ctx.parsed.y ? ctx.parsed.y.toLocaleString() : 'N/A')
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { maxTicksLimit: 8, maxRotation: 0, font: { size: 11 } },
                            grid: { display: false }
                        },
                        y: {
                            ticks: {
                                callback: v => '₩' + v.toLocaleString(),
                                font: { size: 11 }
                            }
                        }
                    }
                }
            });
        }

        function loadPriceChart(period) {
            document.querySelectorAll('.period-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.period === period);
            });
            document.getElementById('price-chart-error').innerHTML = '';

            fetch('/api/stock/kr/005930/price-history?period=' + period)
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('price-chart-error').innerHTML =
                            '<span class="error">오류: ' + data.error + '</span>';
                        return;
                    }
                    priceChartData = data;
                    renderPriceChart(data);
                })
                .catch(e => {
                    document.getElementById('price-chart-error').innerHTML =
                        '<span class="error">차트 로드 실패: ' + e.message + '</span>';
                });
        }

        // 페이지 로드 시 기본 달(1m) 차트 표시
        loadPriceChart('1m');

        // DB 상태 확인
        fetch('/api/health')
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
                        <div><strong>기준일:</strong> ${latest.date}</div>
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

                const perAvg = data.industry_avg.per, pbrAvg = data.industry_avg.pbr;
                const perLow = data.per < perAvg, pbrLow = data.pbr < pbrAvg;
                const verdictBasis =
                    '판정 규칙: PER·PBR이 모두 업계평균보다 낮으면 저평가, 모두 높으면 고평가, 그 외 중립\n\n'
                    + 'PER ' + data.per + ' vs 업계 ' + perAvg.toFixed(1) + ' → ' + (perLow ? '낮음(저평가 신호)' : '높음(고평가 신호)') + '\n'
                    + 'PBR ' + data.pbr + ' vs 업계 ' + pbrAvg.toFixed(2) + ' → ' + (pbrLow ? '낮음(저평가 신호)' : '높음(고평가 신호)') + '\n\n'
                    + '→ 종합 판정: ' + data.verdict;

                document.getElementById('financial-analysis').innerHTML = `
                    <div style="margin-top: 15px;">
                        <div style="margin-bottom: 20px;">
                            <strong style="font-size: 18px;">판정 결과</strong><span class="tooltip-icon" data-tooltip="${verdictBasis}">?</span>
                            <div class="verdict-badge ${verdictClass}" style="font-size: 16px;">
                                ${data.verdict}
                            </div>
                            <div style="font-size: 12px; color: #7f8c8d; margin-top: 6px;">기준일: ${data.as_of || '-'}</div>
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
                            <div style="font-size: 12px; color: #7f8c8d; margin-top: 6px;">기준일: ${data.as_of || '-'}</div>
                        </div>

                        <div class="metrics-grid">
                            <div class="metric-box">
                                <div class="metric-label">
                                    RSI (14주기)
                                    <span class="tooltip-icon" data-tooltip="상대강도지수: 0~100 범위에서 매도/매수 과열 정도를 나타냄">?</span>
                                </div>
                                <div class="metric-value">${data.rsi.toFixed(2)}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    ${data.rsi < 30 ? '과매도' : (data.rsi > 70 ? '과매수' : '중립')}
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">
                                    이동평균선 20일
                                    <span class="tooltip-icon" data-tooltip="최근 20일간의 평균 가격. 단기 추세를 나타냄">?</span>
                                </div>
                                <div class="metric-value">${data.ma_20.toLocaleString()}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    ${data.ma_20 > data.ma_50 ? '↑ 상승추세' : '↓ 하락추세'}
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">
                                    이동평균선 50일
                                    <span class="tooltip-icon" data-tooltip="최근 50일간의 평균 가격. 중기 추세와 지지/저항선 역할">?</span>
                                </div>
                                <div class="metric-value">${data.ma_50.toLocaleString()}</div>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                                    기준선
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">
                                    MACD 히스토그램
                                    <span class="tooltip-icon" data-tooltip="MACD 지수이동평균: 단기와 중기 추세의 교차점을 통해 신호 감지">?</span>
                                </div>
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
                                <div class="comparison-title">
                                    📊 기술적 지표
                                    <span class="tooltip-icon" data-tooltip="MACD(Moving Average Convergence Divergence)는 단기와 중기 이동평균의 차이를 통해 추세 변화를 감지하는 지표">?</span>
                                </div>
                                <div style="font-size: 12px; line-height: 1.8; color: #495057;">
                                    <div>
                                        <strong>MACD Line:</strong> ${data.macd.line.toFixed(2)}
                                        <span class="tooltip-icon" data-tooltip="12일 EMA - 26일 EMA">?</span>
                                    </div>
                                    <div>
                                        <strong>Signal:</strong> ${data.macd.signal.toFixed(2)}
                                        <span class="tooltip-icon" data-tooltip="MACD의 9일 EMA (신호선)">?</span>
                                    </div>
                                    <div>
                                        <strong>Histogram:</strong> ${data.macd.histogram.toFixed(2)}
                                        <span class="tooltip-icon" data-tooltip="MACD Line - Signal의 차이 (양수=상승, 음수=하락)">?</span>
                                    </div>
                                </div>
                            </div>
                            <div class="comparison-card">
                                <div class="comparison-title">
                                    📈 볼린저밴드 (20, 2σ)
                                    <span class="tooltip-icon" data-tooltip="이동평균을 중심으로 표준편차 범위의 상/하단선. 가격 변동성을 나타냄">?</span>
                                </div>
                                <div style="font-size: 12px; line-height: 1.8; color: #495057;">
                                    <div>
                                        <strong>상단:</strong> ${data.bollinger_band.upper.toLocaleString()}
                                        <span class="tooltip-icon" data-tooltip="저항선(과매수 신호)">?</span>
                                    </div>
                                    <div>
                                        <strong>중단:</strong> ${data.bollinger_band.middle.toLocaleString()}
                                        <span class="tooltip-icon" data-tooltip="20일 이동평균선">?</span>
                                    </div>
                                    <div>
                                        <strong>하단:</strong> ${data.bollinger_band.lower.toLocaleString()}
                                        <span class="tooltip-icon" data-tooltip="지지선(과매도 신호)">?</span>
                                    </div>
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
