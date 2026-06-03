#!/usr/bin/env python3
"""
週次実行スクリプト: 株価取得 → AI分析 → スクリーンショット → X投稿
python backend/generate_and_post.py
"""
import os
import sys
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def get_next_friday() -> str:
    now = datetime.now()
    days = (4 - now.weekday()) % 7
    if days == 0:
        days = 7
    nf = now + timedelta(days=days)
    return f"{nf.month}月{nf.day}日（金）"


def get_edition_number() -> int:
    base = datetime(2026, 6, 8)
    return max(1, (datetime.now() - base).days // 7 + 1)


def screenshot(html_content: str, out_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    tmp = Path(tempfile.mkdtemp())
    html_file = tmp / "newspaper.html"
    html_file.write_text(html_content, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 900})
        page.goto(f"file://{html_file.as_posix()}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        el = page.query_selector(".newspaper")
        if el:
            el.screenshot(path=str(out_path))
        else:
            page.screenshot(path=str(out_path), full_page=True)
        browser.close()


def post_to_x(png_path: Path, data: dict, next_friday: str) -> None:
    import tweepy
    key    = os.environ["X_API_KEY"]
    secret = os.environ["X_API_SECRET"]
    token  = os.environ["X_ACCESS_TOKEN"]
    tsec   = os.environ["X_ACCESS_SECRET"]

    auth   = tweepy.OAuth1UserHandler(key, secret, token, tsec)
    v1     = tweepy.API(auth)
    media  = v1.media_upload(filename=str(png_path))

    buy_names  = "・".join(s["name"] for s in data.get("hot_stocks_buy",  []))
    sell_names = "・".join(s["name"] for s in data.get("hot_stocks_sell", []))
    tweet = (
        f"📰 未来株価新聞 第{data['edition_number']}号\n"
        f"━━━━━━━━━━━━\n"
        f"🗓 {next_friday} 15:00 株価予想\n\n"
        f"📈 注目買い銘柄\n{buy_names}\n\n"
        f"📉 注目売り銘柄\n{sell_names}\n\n"
        f"#未来株価新聞 #日本株 #株価予想 #AI投資"
    )
    client = tweepy.Client(
        consumer_key=key, consumer_secret=secret,
        access_token=token, access_token_secret=tsec,
    )
    resp = client.create_tweet(text=tweet, media_ids=[media.media_id])
    print(f"    投稿 URL: https://x.com/i/web/status/{resp.data['id']}")


def main():
    from stock_fetcher import get_stock_data
    from ai_analyzer import analyze_and_generate_newspaper
    from jinja2 import Environment, FileSystemLoader

    next_friday    = get_next_friday()
    edition_number = get_edition_number()
    now            = datetime.now()
    edition_date   = f"{now.year}年{now.month}月{now.day}日"

    print(f"=== 未来株価新聞 第{edition_number}号 ===")
    print(f"    予想対象: {next_friday} 15:00")

    print("1/4 株価データ取得中...")
    stocks = get_stock_data()
    print(f"    {len(stocks)}銘柄取得完了")

    print("2/4 AI分析中...")
    analysis = analyze_and_generate_newspaper(stocks, target_date=f"{next_friday} 15:00")
    print("    完了")

    data = {
        "edition_number": edition_number,
        "edition_date":   edition_date,
        "next_friday":    next_friday,
        **analysis,
    }

    print("3/4 スクリーンショット生成中...")
    tmpl_dir  = Path(__file__).parent / "templates"
    env       = Environment(loader=FileSystemLoader(str(tmpl_dir)))
    html      = env.get_template("newspaper.html").render(**data)
    out_dir   = Path(__file__).parent / "data"
    out_dir.mkdir(exist_ok=True)
    png_path  = out_dir / f"newspaper_{now.strftime('%Y%m%d')}.png"
    screenshot(html, png_path)
    print(f"    保存: {png_path}")

    print("4/4 X投稿中...")
    if os.environ.get("X_API_KEY"):
        post_to_x(png_path, data, next_friday)
        print("    投稿完了!")
    else:
        print("    X_API_KEY 未設定のため投稿スキップ（PNG のみ生成済み）")

    print("=== 完了 ===")


if __name__ == "__main__":
    main()
