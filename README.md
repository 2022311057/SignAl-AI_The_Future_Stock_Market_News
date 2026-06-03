# 未来株価新聞 ― AI×日本株 週次予測レポート自動生成システム

> 東証主要30銘柄の株価データをリアルタイム取得し、大規模言語モデルによるテクニカル分析を経て、  
> 新聞レイアウトの画像を自動生成・SNS投稿まで行うフルスタック自動化システム。

---

## 概要

毎週日曜日 18:00（JST）に GitHub Actions が自動起動し、以下のパイプラインをノーコードで実行します。

```
Yahoo Finance → 株価取得 → Groq AI 分析 → Jinja2 HTML 生成 → Playwright スクリーンショット → X（Twitter）投稿
```

人手を一切介さず、データ取得から SNS 投稿まで完結します。

---

## 画面イメージ

| React プレビュー画面 | 生成 PNG（投稿用） |
|---|---|
| ブラウザでリアルタイム確認 | GitHub Actions Artifacts に保存 |

---

## 主な機能

- **リアルタイム株価取得** — Yahoo Finance API（yfinance）で東証30銘柄の株価・出来高・財務指標を取得
- **AI による市場分析** — Groq API（Llama 3.3-70B）が注目買い銘柄 / 売り銘柄を各3社選定し、記事・見出し・リスク注記を生成
- **1週間後の株価予測** — 現在株価・週次変化率・テクニカル水準をもとに、次週金曜日 15:00 の予想株価を整数で算出
- **新聞レイアウト自動生成** — Jinja2 テンプレートで本格的な紙面レイアウトを HTML 生成し、Playwright でピクセルパーフェクトな PNG に変換
- **完全自動 SNS 投稿** — Tweepy（X API v2）で生成画像を週次投稿
- **Web プレビュー画面** — React + Vite で構築したブラウザ確認用 UI（手動更新・PNG ダウンロード機能付き）

---

## 技術スタック

### バックエンド
| 技術 | 用途 |
|---|---|
| Python 3.11 | メイン言語 |
| FastAPI | REST API サーバー |
| yfinance | 東証株価データ取得 |
| Groq API / Llama 3.3-70B | AI 分析・記事生成 |
| Jinja2 | HTML テンプレートエンジン |
| Playwright | ヘッドレスブラウザによる PNG スクリーンショット |
| Tweepy | X（Twitter）API v1/v2 投稿 |
| APScheduler | アプリ内スケジューラ（週次 Cron） |

### フロントエンド
| 技術 | 用途 |
|---|---|
| React 18 + TypeScript | プレビュー UI |
| Vite | ビルドツール |
| html-to-image | ブラウザから直接 PNG 保存 |

### インフラ・自動化
| 技術 | 用途 |
|---|---|
| GitHub Actions | 毎週日曜 18:00 JST 自動実行（cron） |
| Docker / Docker Compose | ローカル開発環境 |
| GitHub Secrets | API キー管理（セキュア） |

---

## システム構成図

```
[GitHub Actions: 毎週日曜 18:00 JST]
         │
         ▼
┌─────────────────────────────────┐
│  generate_and_post.py           │
│                                 │
│  1. yfinance → 30銘柄取得       │
│  2. Groq API → AI分析・記事生成 │
│  3. Jinja2  → HTML生成          │
│  4. Playwright → PNG変換        │
│  5. Tweepy  → X投稿             │
└─────────────────────────────────┘
         │
         ▼
   X（Twitter）に自動投稿
   GitHub Artifacts に PNG 保存
```

---

## 工夫した点

### 1. LLM プロンプト設計
Groq API へのリクエストを最適化するため、送信データを必要フィールドのみに絞り（上位20銘柄、8フィールド）、トークン消費を削減しながら高精度な分析を実現。JSON スキーマを厳密に指定することで、パース失敗を防止しています。

### 2. サーバーレス画像生成
React + Vite の Web サーバーを起動せず、Jinja2 + Playwright のみで完結する画像生成パイプラインを設計。GitHub Actions の Ubuntu 環境でも日本語フォント（Noto CJK）を確実に表示するため、`apt-get` によるフォントインストールと Google Fonts の読み込み待機（3000ms）を組み合わせています。

### 3. セキュリティ設計
API キー類は `.env`（ローカル）と GitHub Secrets（CI/CD）で管理し、ソースコードへの直接埋め込みを完全排除。`.gitignore` で `.env` ファイルのコミットも防止しています。

### 4. フォールバック機構
Groq API が利用不可の場合でも、統計ベースのフォールバックデータ生成により新聞の出力を継続できる設計にしています。

---

## セットアップ

### 前提条件
- Python 3.11+
- Node.js 18+
- Docker（任意）

### ローカル実行

```bash
# 依存関係インストール
pip install -r ai-newspaper/backend/requirements.txt
playwright install chromium

# 環境変数設定
cp ai-newspaper/.env.example ai-newspaper/.env
# .env に GROQ_API_KEY を記入

# PNG 生成（Web サーバー不要）
python ai-newspaper/backend/generate_and_post.py
```

### Docker 実行

```bash
cd ai-newspaper
docker compose up
# http://localhost:5173 でプレビュー確認
```

### GitHub Actions 自動実行

1. リポジトリを GitHub に push
2. Settings → Secrets → Actions で以下を設定

| Secret 名 | 説明 |
|---|---|
| `GROQ_API_KEY` | Groq API キー |
| `X_API_KEY` | X API Key（Consumer Key） |
| `X_API_SECRET` | X API Secret |
| `X_ACCESS_TOKEN` | X Access Token |
| `X_ACCESS_SECRET` | X Access Token Secret |

毎週日曜 18:00 JST に自動実行。Actions タブから手動実行も可能。

---

## ディレクトリ構成

```
.
├── .github/
│   └── workflows/
│       └── weekly_post.yml        # GitHub Actions ワークフロー
└── ai-newspaper/
    ├── backend/
    │   ├── main.py                # FastAPI + APScheduler
    │   ├── stock_fetcher.py       # yfinance 株価取得
    │   ├── ai_analyzer.py         # Groq API 分析・記事生成
    │   ├── generate_and_post.py   # 単体実行スクリプト（PNG生成・X投稿）
    │   ├── models.py              # Pydantic モデル
    │   ├── templates/
    │   │   └── newspaper.html     # Jinja2 新聞テンプレート
    │   └── requirements.txt
    └── frontend/
        ├── src/
        │   ├── App.tsx            # メインコンポーネント
        │   └── index.css          # 新聞スタイル
        └── package.json
```

---

## 対象銘柄（東証主要30銘柄）

トヨタ自動車 / ソニーグループ / 三菱UFJフィナンシャル / ソフトバンクグループ / キーエンス /  
ファナック / 信越化学工業 / 東京エレクトロン / リクルートHD / 任天堂 /  
中外製薬 / NTT / 三井住友FG / ダイキン工業 / 本田技研工業 /  
日立製作所 / KDDI / オリエンタルランド / キヤノン / 富士通 /  
武田薬品工業 / みずほFG / 三菱電機 / ブリヂストン / 三菱商事 /  
ニデック / 三菱重工業 / レーザーテック / 第一三共 / ファーストリテイリング

---

## 注意事項

本システムが出力する情報は、AI による分析に基づく参考情報です。  
投資判断はご自身の責任において行ってください。

---

## 使用 API・サービス

- [Groq API](https://groq.com/) — LLM 推論（Llama 3.3-70B, 無料枠）
- [Yahoo Finance / yfinance](https://github.com/ranaroussi/yfinance) — 株価データ（無料）
- [X Developer API](https://developer.twitter.com/) — SNS 投稿
- [GitHub Actions](https://github.com/features/actions) — CI/CD・定期実行（無料枠）
