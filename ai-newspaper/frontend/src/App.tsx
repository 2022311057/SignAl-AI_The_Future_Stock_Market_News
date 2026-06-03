import { useState, useEffect, useRef, useCallback } from 'react'
import { toPng } from 'html-to-image'

interface StockArticle {
  ticker: string
  name: string
  sector_jp: string
  market_cap_str: string
  current_price: number
  predicted_price_1week: number
  price_change: number
  headline: string
  article: string
  risk_note: string
  outlook_1week: string
  recommendation: string
  confidence: string
  reason: string
}

interface NewspaperData {
  edition_date: string
  edition_number: number
  market_summary: string
  target_date?: string
  hot_stocks_buy: StockArticle[]
  hot_stocks_sell: StockArticle[]
}

function recClass(rec: string) {
  if (rec.includes('強い買い')) return 'rec-strong-buy'
  if (rec.includes('買い')) return 'rec-buy'
  if (rec.includes('強い売り')) return 'rec-strong-sell'
  if (rec.includes('売り')) return 'rec-sell'
  return 'rec-neutral'
}

function ArticleBlock({ stock, rank, targetDate }: { stock: StockArticle; rank: number; targetDate: string }) {
  const up = stock.price_change >= 0
  const predicted = stock.predicted_price_1week ?? Math.round(stock.current_price * (1 + stock.price_change / 100))
  return (
    <article className="article-block">
      {/* 銘柄名ヘッダー */}
      <div className="article-company-header">
        <div className="article-company-top">
          <h2 className="article-company-name">{stock.name}</h2>
          <span className={`rec-badge ${recClass(stock.recommendation)}`}>{stock.recommendation}</span>
        </div>
        <div className="article-company-meta">
          <span className="article-rank">第{rank}位</span>
          <span className="article-sector">{stock.sector_jp}</span>
          <span className="article-ticker">{stock.ticker}</span>
          <span className="article-confidence">確度: {stock.confidence}</span>
        </div>
      </div>

      {/* 見出し */}
      <h3 className="article-headline">{stock.headline}</h3>

      {/* 株価比較 */}
      <div className="article-price-comparison">
        <div className="price-block">
          <span className="price-label">現在値</span>
          <span className="article-price">¥{stock.current_price.toLocaleString()}</span>
        </div>
        <span className="price-arrow">→</span>
        <div className="price-block">
          <span className="price-label">{targetDate} 15:00予想</span>
          <span className={`article-price-predicted ${up ? 'up' : 'down'}`}>
            ¥{predicted.toLocaleString()}
          </span>
          <span className={`article-change ${up ? 'up' : 'down'}`}>
            {up ? '▲' : '▼'}{Math.abs(stock.price_change).toFixed(2)}%
          </span>
        </div>
        <span className="article-mktcap price-mktcap">時価総額 {stock.market_cap_str}</span>
      </div>

      <p className="article-body">{stock.article}</p>
      {stock.risk_note && (
        <div className="article-risk">⚠ {stock.risk_note}</div>
      )}
      <div className="outlook-card">
        <span className="outlook-card-label">【{targetDate} 15:00の見通し】</span>
        <span className="outlook-card-text">{stock.outlook_1week}</span>
      </div>
      <div className="article-reason">▶ 選定理由: {stock.reason}</div>
    </article>
  )
}

export default function App() {
  const [data, setData] = useState<NewspaperData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [updating, setUpdating] = useState(false)
  const paperRef = useRef<HTMLDivElement>(null)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/newspaper')
      if (res.status === 404) { setError('生成中'); return }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail ?? `HTTP ${res.status}`)
      }
      setData(await res.json())
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : '不明なエラー')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const id = setInterval(fetchData, 60000)
    return () => clearInterval(id)
  }, [fetchData])

  const handleSave = async () => {
    if (!paperRef.current || !data) return
    setSaving(true)
    try {
      const url = await toPng(paperRef.current, {
        pixelRatio: 2,
        backgroundColor: '#f5f0e8',
        skipFonts: false,
      })
      const a = document.createElement('a')
      a.download = `未来株価新聞_第${data.edition_number}号.png`
      a.href = url
      a.click()
    } catch (e) {
      console.error(e)
    } finally {
      setSaving(false)
    }
  }

  const handleUpdate = async () => {
    if (updating) return
    setUpdating(true)
    await fetch('/api/newspaper/update', { method: 'POST' })
    setTimeout(() => { fetchData(); setUpdating(false) }, 30000)
  }

  const editionDate = data
    ? new Date(data.edition_date).toLocaleDateString('ja-JP', {
        year: 'numeric', month: 'long', day: 'numeric', weekday: 'long',
      })
    : ''

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>未来株価新聞を読み込み中...</p>
      </div>
    )
  }

  return (
    <div className="app-shell">
      {/* コントロールバー（画像に含まれない） */}
      <div className="control-bar">
        <button className="btn-save" onClick={handleSave} disabled={saving || !data}>
          {saving ? '⏳ 生成中...' : '📥 画像として保存'}
        </button>
        <button className="btn-update" onClick={handleUpdate} disabled={updating}>
          {updating ? '⏳ 更新中...' : '🔄 今すぐ更新'}
        </button>
        {data && <span className="control-hint">毎日 07:00 JST 自動更新 ／ 保存した画像をSNSで共有できます ／ 未来株価新聞</span>}
      </div>

      {error === '生成中' ? (
        <div className="status-box">⏳ AI分析中... 数分後に自動更新されます</div>
      ) : error ? (
        <div className="status-box error">エラー: {error}</div>
      ) : data ? (
        /* ─── 新聞本体（PNG保存対象） ─── */
        <div className="newspaper" ref={paperRef}>

          {/* 題字エリア */}
          <header className="masthead">
            <div className="masthead-eyebrow">東 証 銘 柄 × A I 予 測 ／ 株 価 未 来 分 析 専 門 紙</div>
            <h1 className="masthead-title">未 来 株 価 新 聞</h1>
            <div className="masthead-rule" />
            <div className="masthead-meta">
              <span>{editionDate}</span>
              <span className="masthead-edition">第 {data.edition_number} 号</span>
              <span>Yahoo Finance × Groq AI（無料）</span>
            </div>
          </header>

          {/* 市場概況 */}
          <section className="market-summary-bar">
            <span className="summary-kicker">◆ 市場概況 ◆</span>
            <span className="summary-body">{data.market_summary}</span>
          </section>

          {/* 2カラム本文 */}
          <div className="columns-wrapper">
            {/* 左列：買い注目銘柄 */}
            <div className="news-col">
              <div className="col-kicker col-kicker-buy">次 週 金 曜 注 目 買 い 銘 柄</div>
              <div className="col-kicker-sub">— {data.target_date ?? '次週金曜日'} 15:00 上 昇 予 想 —</div>
              {(data.hot_stocks_buy ?? []).map((s, i) => (
                <ArticleBlock key={`buy-${s.ticker}`} stock={s} rank={i + 1} targetDate={data.target_date ?? '次週金曜日'} />
              ))}
            </div>

            <div className="col-divider" />

            {/* 右列：売り注目銘柄 */}
            <div className="news-col">
              <div className="col-kicker col-kicker-sell">次 週 金 曜 注 目 売 り 銘 柄</div>
              <div className="col-kicker-sub col-kicker-sub-sell">— {data.target_date ?? '次週金曜日'} 15:00 下 落 予 想 —</div>
              {(data.hot_stocks_sell ?? []).map((s, i) => (
                <ArticleBlock key={`sell-${s.ticker}`} stock={s} rank={i + 1} targetDate={data.target_date ?? '次週金曜日'} />
              ))}
            </div>
          </div>

          {/* フッター */}
          <footer className="paper-footer">
            <span>本紙の情報は投資判断の参考情報であり、投資を推奨するものではありません。最終判断はご自身でお願いします。</span>
            <span>AI分析: Groq（Llama 3.3-70B）　データ提供: Yahoo Finance</span>
          </footer>
        </div>
      ) : null}
    </div>
  )
}
