from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class StockAnalysis(BaseModel):
    ticker: str
    name: str
    current_price: float
    price_change: float
    headline: str
    article: str
    outlook_1month: str
    outlook_6months: str
    outlook_1year: str
    recommendation: str
    confidence: str
    reason: str


class NewspaperEdition(BaseModel):
    edition_date: datetime
    edition_number: int
    update_frequency: str
    market_summary: str
    hot_stocks_1month: List[StockAnalysis]
    hot_stocks_6months: List[StockAnalysis]
    hot_stocks_1year: List[StockAnalysis]
