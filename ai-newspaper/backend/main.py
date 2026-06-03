import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_analyzer import analyze_and_generate_newspaper
from stock_fetcher import JAPANESE_STOCKS, get_stock_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_FILE = DATA_DIR / "newspaper.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UPDATE_FREQUENCY = os.environ.get("UPDATE_FREQUENCY", "daily")

scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
is_updating = False


def get_next_friday_str() -> str:
    now = datetime.now()
    days_until_friday = (4 - now.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    nf = now + timedelta(days=days_until_friday)
    return f"{nf.month}月{nf.day}日（金）"


def get_next_edition_number() -> int:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("edition_number", 0) + 1
        except Exception:
            pass
    return 1


def update_newspaper():
    global is_updating
    if is_updating:
        logger.info("Update already in progress, skipping")
        return

    is_updating = True
    try:
        logger.info("Starting newspaper update...")
        stocks_data = get_stock_data(JAPANESE_STOCKS)

        if not stocks_data:
            logger.error("No stock data fetched")
            return

        next_friday = get_next_friday_str()
        logger.info(f"Fetched {len(stocks_data)} stocks, running AI analysis (target: {next_friday} 15:00)...")
        analysis = analyze_and_generate_newspaper(stocks_data, target_date=f"{next_friday} 15:00")

        newspaper_data = {
            "edition_date": datetime.now().isoformat(),
            "edition_number": get_next_edition_number(),
            "update_frequency": UPDATE_FREQUENCY,
            "stocks_count": len(stocks_data),
            "target_date": next_friday,
            **analysis,
        }

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(newspaper_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Newspaper edition #{newspaper_data['edition_number']} published")

    except Exception as e:
        logger.error(f"Failed to update newspaper: {e}", exc_info=True)
    finally:
        is_updating = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: 毎週日曜 18:00 JST
    scheduler.add_job(
        update_newspaper,
        CronTrigger(day_of_week="sun", hour=18, minute=0),
        id="newspaper_update",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: 毎週日曜 18:00 JST")

    if not DATA_FILE.exists():
        logger.info("No existing data, generating first edition in background...")
        import threading
        threading.Thread(target=update_newspaper, daemon=True).start()

    yield

    # 終了時
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(title="AI未来新聞 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/newspaper")
async def get_newspaper():
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="新聞データを生成中です。初回生成には数分かかります。",
        )
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/newspaper/update")
async def trigger_update(background_tasks: BackgroundTasks):
    if is_updating:
        return {"message": "更新中です。しばらくお待ちください。", "status": "already_updating"}
    background_tasks.add_task(update_newspaper)
    return {"message": "新聞の更新を開始しました（数分かかります）", "status": "updating"}


@app.get("/api/status")
async def get_status():
    last_update = None
    edition_number = None
    if DATA_FILE.exists():
        last_update = datetime.fromtimestamp(DATA_FILE.stat().st_mtime).isoformat()
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                edition_number = data.get("edition_number")
        except Exception:
            pass

    return {
        "status": "running",
        "update_frequency": UPDATE_FREQUENCY,
        "is_updating": is_updating,
        "has_data": DATA_FILE.exists(),
        "last_update": last_update,
        "edition_number": edition_number,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
