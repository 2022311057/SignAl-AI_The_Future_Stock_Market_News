import json
import os
import logging
from typing import List, Dict

from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)


def _fmt_mktcap(mktcap) -> str:
    """時価総額を兆円・億円表記に変換"""
    if not mktcap:
        return "N/A"
    try:
        v = float(mktcap)
        if v >= 1e12:
            return f"{v/1e12:.1f}兆円"
        if v >= 1e8:
            return f"{v/1e8:.0f}億円"
        return f"{v:,.0f}円"
    except Exception:
        return "N/A"


def analyze_and_generate_newspaper(stocks_data: List[Dict], target_date: str = "次週金曜日 15:00") -> Dict:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        logger.error("GROQ_API_KEY が設定されていません。")
        return _generate_fallback_data(stocks_data, target_date)

    client = Groq(api_key=api_key)

    # 必要フィールドのみ・上位20銘柄に絞りトークン削減
    slim_data = [
        {
            "ticker": s["ticker"],
            "name": s["name"],
            "sector_jp": s.get("sector_jp", "その他"),
            "price": s["current_price"],
            "mktcap": _fmt_mktcap(s.get("market_cap")),
            "chg_1d": s.get("price_change_1d"),
            "chg_1w": s.get("price_change_1w"),
            "chg_1m": s.get("price_change_1m"),
            "vol_ratio": s.get("volume_ratio"),
            "per": s.get("pe_ratio"),
            "high52w": s.get("week_52_high"),
            "low52w": s.get("week_52_low"),
        }
        for s in stocks_data
    ][:20]

    stocks_summary = json.dumps(slim_data, ensure_ascii=False, default=str)

    prompt = f"""あなたは日本の著名な株式アナリストで、未来株価新聞の編集長です。
以下の東証銘柄データを厳密に分析し、リアルで詳細な新聞記事を生成してください。

## 株価データ
{stocks_summary}

## 予想対象日時
{target_date}（東京証券取引所 後場引け）

## 分析の原則（必ず守ること）
1. **hot_stocks_buy**: {target_date}に上昇が期待できる「買い」推奨銘柄を3つ選ぶ。recommendation は「強い買い」または「買い」のみ。
2. **hot_stocks_sell**: {target_date}に下落・調整リスクがある「売り/警戒」銘柄を3つ選ぶ。recommendation は「強い売り」または「売り」のみ。
3. **買いと売りで異なる銘柄を選ぶこと**（重複禁止）。
4. **根拠を数値で示す**: 株価・変化率・出来高比率・PER・52週高安値位置を必ず記事に含める。
5. **市場時価総額を活用**: mktcap（時価総額）を market_cap_str フィールドにそのまま使う。
6. **predicted_price_1week**: 現在株価・週次変化率・テクニカル水準をもとに{target_date}の予想終値を算出して数値で示す（整数）。
7. **sector_jp**: データの sector_jp フィールドをそのまま使う。

## 評価の指針（買い選定）
- chg_1w が正 かつ vol_ratio > 1.3: モメンタム買い
- 52週安値圏からの反発: 底打ち期待
- PER が業種平均より低い: バリュー買い
- chg_1m がプラス転換直後: トレンド転換買い

## 評価の指針（売り選定）
- chg_1w > 8% かつ vol_ratio > 1.8: 短期過熱・利確売り
- 52週高値圏（高値の96%以上）: 上値抵抗で反落リスク
- PER > 40 かつ成長鈍化兆候: 割高売り
- chg_1d が大幅プラス後: 出尽くし売り

## 出力形式（JSON のみ・余分なテキスト禁止）
{{
  "market_summary": "市場全体の現況と今後の見通し（200文字程度、具体的な数値・セクター動向・リスク要因を含む）",
  "hot_stocks_buy": [
    {{
      "ticker": "銘柄コード",
      "name": "銘柄名",
      "sector_jp": "日本語業種（データのsector_jpをそのまま）",
      "market_cap_str": "時価総額（mktcapの値をそのまま）",
      "current_price": 株価（数値）,
      "predicted_price_1week": {target_date}の予想株価（整数・テクニカル分析で算出）,
      "price_change": 予想変化率（数値%・現在株価から{target_date}への予想変化率）,
      "headline": "見出し（20文字以内・上昇期待を表す力強い表現）",
      "article": "記事本文（180〜220文字・株価水準・週次変化率・出来高比率・PER・52週高安値位置・上昇の背景と根拠を詳述）",
      "risk_note": "リスク要因（50〜70文字・買い推奨でも必ず何らかのリスクを具体的に記載）",
      "outlook_1week": "{target_date}の見通し（40〜50文字・上昇幅の目安や条件を含む）",
      "recommendation": "強い買い または 買い",
      "confidence": "高/中/低",
      "reason": "選定理由（30文字以内・この銘柄固有の理由）"
    }}
  ],
  "hot_stocks_sell": [
    {{
      "ticker": "銘柄コード",
      "name": "銘柄名",
      "sector_jp": "日本語業種（データのsector_jpをそのまま）",
      "market_cap_str": "時価総額（mktcapの値をそのまま）",
      "current_price": 株価（数値）,
      "predicted_price_1week": {target_date}の予想株価（整数・テクニカル分析で算出）,
      "price_change": 予想変化率（数値%・現在株価から{target_date}への予想変化率）,
      "headline": "見出し（20文字以内・下落リスクを表す力強い表現）",
      "article": "記事本文（180〜220文字・株価水準・週次変化率・出来高比率・PER・52週高安値位置・下落リスクの根拠を詳述）",
      "risk_note": "下落シナリオ（50〜70文字・具体的な下落トリガーや支持線を記載）",
      "outlook_1week": "{target_date}の見通し（40〜50文字・下落幅の目安や反発条件を含む）",
      "recommendation": "強い売り または 売り",
      "confidence": "高/中/低",
      "reason": "選定理由（30文字以内・売り選定の固有理由）"
    }}
  ]
}}

重要制約:
- hot_stocks_buy と hot_stocks_sell は必ず各3銘柄。
- 両リストで同じ銘柄を使ってはならない（完全に異なる6銘柄）。
- JSON以外のテキストは絶対に含めないこと。"""

    logger.info("Calling Groq API...")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "日本株専門アナリスト。JSON形式のみで回答。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3500,
            temperature=0.3,
        )
    except Exception as e:
        logger.error(f"Groq API失敗: {e}")
        return _generate_fallback_data(stocks_data)

    response_text = response.choices[0].message.content
    logger.info(f"Groq response: {len(response_text)} chars")

    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON")
        result = json.loads(response_text[start:end])
        logger.info("AI response parsed successfully")
        return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"JSON parse error: {e}")
        return _generate_fallback_data(stocks_data, target_date)


def _generate_fallback_data(stocks_data: List[Dict], target_date: str = "次週金曜日 15:00") -> Dict:
    by_gain = sorted(stocks_data, key=lambda x: x.get("price_change_1w", 0), reverse=True)[:3]
    by_loss = sorted(stocks_data, key=lambda x: x.get("price_change_1w", 0))[:3]

    def entry(s: Dict, is_sell: bool) -> Dict:
        chg = s.get("price_change_1w", 0) or 0
        price = s["current_price"]
        predicted = round(price * (1 + chg / 100))
        return {
            "ticker": s["ticker"],
            "name": s["name"],
            "sector_jp": s.get("sector_jp", "その他"),
            "market_cap_str": _fmt_mktcap(s.get("market_cap")),
            "current_price": price,
            "predicted_price_1week": predicted,
            "price_change": round(chg, 2),
            "headline": f"{s['name']}{'に売り圧力' if is_sell else 'に上昇期待'}",
            "article": f"GROQ_API_KEYを.envに設定するとAI分析が有効になります。現在株価¥{price:,.0f}、週次変化率{chg:+.1f}%。",
            "risk_note": "APIキー未設定のためリスク分析を表示できません。",
            "outlook_1week": "APIキー設定後に表示",
            "recommendation": "強い売り" if is_sell else "買い",
            "confidence": "低",
            "reason": "データ取得成功・AI分析待機中",
        }

    return {
        "market_summary": "⚠️ GROQ_API_KEYが未設定のため、AI分析は無効です。groq.comで無料APIキーを取得してください。株価データは正常に取得されています。",
        "hot_stocks_buy": [entry(s, False) for s in by_gain],
        "hot_stocks_sell": [entry(s, True) for s in by_loss],
    }
