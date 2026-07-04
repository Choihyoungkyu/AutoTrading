// 백엔드 REST API 호출 래퍼.
// 개발: Vite 프록시가 /api·/analyze를 Flask(8000)로 전달.
// 배포: Flask가 SPA와 API를 같은 출처에서 서빙하므로 base path 불필요.
export async function getJson(path) {
  const res = await fetch(path)
  return res.json()
}

export const STOCK_CODE = '005930'

export const api = {
  health: () => getJson('/api/health'),
  search: (q) => getJson(`/search?q=${encodeURIComponent(q)}`),
  krxStock: (code = STOCK_CODE) => getJson(`/api/stock/kr/${code}`),
  priceHistory: (period, code = STOCK_CODE) =>
    getJson(`/api/stock/kr/${code}/price-history?period=${period}`),
  financial: (code = STOCK_CODE) => getJson(`/analyze/${code}/financial`),
  chart: (code = STOCK_CODE) => getJson(`/analyze/${code}/chart`),
  news: (code = STOCK_CODE) => getJson(`/analyze/${code}/news`),
  recommendation: (code = STOCK_CODE) => getJson(`/analyze/${code}/recommendation`),
  priceTarget: (expectedReturn, maxLoss, code = STOCK_CODE) =>
    getJson(`/analyze/${code}/price-target?expected_return=${expectedReturn}&max_loss=${maxLoss}`),
}
