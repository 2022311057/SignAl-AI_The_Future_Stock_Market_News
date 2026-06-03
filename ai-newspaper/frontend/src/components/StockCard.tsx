interface StockAnalysis {
  ticker: string
  name: string
  current_price: number
  price_change: number
  headline: string
  article: string
  outlook_1month: string
  outlook_6months: string
  outlook_1year: string
  recommendation: string
  confidence: string
  reason: string
}

interface Props {
  stock: StockAnalysis
  selectedPeriod: '1month' | '6months' | '1year'
  rank: number
}

function getBadgeClass(rec: string): string {
  if (rec === '強い買い') return 'badge-strong-buy'
  if (rec === '買い') return 'badge-buy'
  if (rec === '中立') return 'badge-neutral'
  if (rec === '売り') return 'badge-sell'
  if (rec === '強い売り') return 'badge-strong-sell'
  return 'badge-neutral'
}

function getPriceChangeClass(change: number): string {
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

export default function StockCard({ stock, selectedPeriod, rank }: Props) {
  const outlook =
    selectedPeriod === '1month'
      ? stock.outlook_1month
      : selectedPeriod === '6months'
      ? stock.outlook_6months
      : stock.outlook_1year

  const outlookLabel =
    selectedPeriod === '1month' ? '1ヶ月後の見通し' : selectedPeriod === '6months' ? '6ヶ月後の見通し' : '1年後の見通し'

  const priceChangeClass = getPriceChangeClass(stock.price_change)
  const changeSign = stock.price_change >= 0 ? '+' : ''

  return (
    <div className="stock-card">
      <div className="stock-card-header">
        <div className="stock-ticker-name">
          <div className="stock-ticker">
            #{rank} &nbsp; {stock.ticker}
          </div>
          <div className="stock-name">{stock.name}</div>
        </div>
        <span className={`recommendation-badge ${getBadgeClass(stock.recommendation)}`}>
          {stock.recommendation}
        </span>
      </div>

      <div className="stock-price-row">
        <div className="stock-price">
          <span className="price-yen">¥</span>
          {stock.current_price.toLocaleString()}
        </div>
        <div className={`price-change ${priceChangeClass}`}>
          {changeSign}{stock.price_change.toFixed(2)}%
        </div>
        <div className="confidence-dot">
          信頼度: {stock.confidence}
        </div>
      </div>

      <div className="stock-headline">「{stock.headline}」</div>

      <div className="stock-article">{stock.article}</div>

      <div className="stock-outlook">
        <span className="outlook-label">{outlookLabel}</span>
        {outlook}
      </div>

      <div className="stock-reason">選定理由: {stock.reason}</div>
    </div>
  )
}
