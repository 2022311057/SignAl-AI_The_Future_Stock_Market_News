import yfinance as yf
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# 銘柄別日本語業種
SECTOR_JP_MAP = {
    "7203.T": "輸送用機器",
    "6758.T": "電気機器",
    "8306.T": "銀行業",
    "9984.T": "情報・通信",
    "6861.T": "電気機器",
    "6954.T": "電気機器",
    "4063.T": "化学",
    "8035.T": "半導体製造装置",
    "6098.T": "サービス業",
    "7974.T": "娯楽・ゲーム",
    "4519.T": "医薬品",
    "9432.T": "情報・通信",
    "8316.T": "銀行業",
    "6367.T": "電気機器",
    "7267.T": "輸送用機器",
    "6501.T": "電気機器",
    "9433.T": "情報・通信",
    "4661.T": "サービス業",
    "7751.T": "電気機器",
    "6702.T": "電気機器",
    "4502.T": "医薬品",
    "8411.T": "銀行業",
    "6503.T": "電気機器",
    "5108.T": "ゴム製品",
    "8058.T": "卸売業",
    "6594.T": "電気機器",
    "7011.T": "機械",
    "6920.T": "半導体製造装置",
    "4568.T": "医薬品",
    "9983.T": "小売業",
}

# 東証主要銘柄（ニッケイ225上位・注目セクター）
JAPANESE_STOCKS = [
    ("7203.T", "トヨタ自動車"),
    ("6758.T", "ソニーグループ"),
    ("8306.T", "三菱UFJフィナンシャル"),
    ("9984.T", "ソフトバンクグループ"),
    ("6861.T", "キーエンス"),
    ("6954.T", "ファナック"),
    ("4063.T", "信越化学工業"),
    ("8035.T", "東京エレクトロン"),
    ("6098.T", "リクルートホールディングス"),
    ("7974.T", "任天堂"),
    ("4519.T", "中外製薬"),
    ("9432.T", "日本電信電話"),
    ("8316.T", "三井住友フィナンシャル"),
    ("6367.T", "ダイキン工業"),
    ("7267.T", "本田技研工業"),
    ("6501.T", "日立製作所"),
    ("9433.T", "KDDI"),
    ("4661.T", "オリエンタルランド"),
    ("7751.T", "キヤノン"),
    ("6702.T", "富士通"),
    ("4502.T", "武田薬品工業"),
    ("8411.T", "みずほフィナンシャル"),
    ("6503.T", "三菱電機"),
    ("5108.T", "ブリヂストン"),
    ("8058.T", "三菱商事"),
    ("6594.T", "ニデック"),
    ("7011.T", "三菱重工業"),
    ("6920.T", "レーザーテック"),
    ("4568.T", "第一三共"),
    ("9983.T", "ファーストリテイリング"),
]


def get_stock_data(tickers_with_names: List[tuple] = None) -> List[Dict]:
    if tickers_with_names is None:
        tickers_with_names = JAPANESE_STOCKS

    tickers = [t[0] for t in tickers_with_names]
    name_map = {t[0]: t[1] for t in tickers_with_names}

    stocks_data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")

            # NaN行（当日未確定分）を除去
            hist = hist.dropna(subset=["Close"])

            if hist.empty or len(hist) < 2:
                logger.warning(f"No data for {ticker}")
                continue

            info = stock.info

            current_price = float(hist["Close"].iloc[-1])
            price_1d_ago = float(hist["Close"].iloc[-2])
            price_1m_ago = float(hist["Close"].iloc[-21]) if len(hist) >= 21 else float(hist["Close"].iloc[0])
            price_3m_ago = float(hist["Close"].iloc[0])

            price_1w_ago = float(hist["Close"].iloc[-5]) if len(hist) >= 5 else price_1m_ago

            price_change_1d = round(((current_price - price_1d_ago) / price_1d_ago) * 100, 2)
            price_change_1w = round(((current_price - price_1w_ago) / price_1w_ago) * 100, 2)
            price_change_1m = round(((current_price - price_1m_ago) / price_1m_ago) * 100, 2)
            price_change_3m = round(((current_price - price_3m_ago) / price_3m_ago) * 100, 2)

            avg_volume = float(hist["Volume"].tail(20).mean())
            latest_volume = float(hist["Volume"].iloc[-1])
            volume_ratio = round(latest_volume / avg_volume, 2) if avg_volume > 0 else 1.0

            stocks_data.append({
                "ticker": ticker,
                "name": name_map.get(ticker, info.get("longName", ticker)),
                "current_price": round(current_price, 0),
                "price_change_1d": price_change_1d,
                "price_change_1w": price_change_1w,
                "price_change_1m": price_change_1m,
                "price_change_3m": price_change_3m,
                "volume_ratio": volume_ratio,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "sector": info.get("sector", "N/A"),
                "sector_jp": SECTOR_JP_MAP.get(ticker, info.get("sector", "その他")),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low": info.get("fiftyTwoWeekLow"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "recent_close_prices": [round(float(p), 0) for p in hist["Close"].tail(10).tolist()],
            })

            logger.info(f"Fetched {ticker}: ¥{current_price:,.0f} ({price_change_1d:+.2f}%)")

        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            continue

    logger.info(f"Successfully fetched {len(stocks_data)}/{len(tickers)} stocks")
    return stocks_data
