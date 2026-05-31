"""Fetch AI-adjacent equity quotes via Finnhub (prod) or yfinance (dev)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

SYMBOLS: dict[str, str] = {
    "NVDA": "NVIDIA",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "META": "Meta",
    "AMZN": "Amazon",
    "AMD": "AMD",
}


def _fetch_finnhub(symbol: str, api_key: str) -> dict[str, Any] | None:
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
    request = Request(url, headers={"User-Agent": "pricing-sentinel/1.0"})
    with urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode())
    if data.get("c") is None:
        return None
    current = float(data["c"])
    prev = float(data.get("pc") or current)
    change_pct = ((current - prev) / prev * 100) if prev else 0.0
    return {
        "symbol": symbol,
        "name": SYMBOLS.get(symbol, symbol),
        "price": current,
        "change_pct": round(change_pct, 2),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {"provider": "finnhub", "delayed": True, "currency": "USD"},
    }


def _fetch_yfinance(symbol: str) -> dict[str, Any] | None:
    try:
        import yfinance as yf
    except ImportError:
        log.warning("yfinance not installed")
        return None
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    current = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
    prev = getattr(info, "previous_close", None) or current
    if current is None:
        hist = ticker.history(period="2d")
        if hist.empty:
            return None
        current = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
    change_pct = ((current - prev) / prev * 100) if prev else 0.0
    return {
        "symbol": symbol,
        "name": SYMBOLS.get(symbol, symbol),
        "price": round(float(current), 2),
        "change_pct": round(change_pct, 2),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {"provider": "yfinance", "delayed": True, "currency": "USD"},
    }


def fetch_equity_quotes() -> list[dict[str, Any]]:
    api_key = os.environ.get("FINNHUB_API_KEY")
    quotes: list[dict[str, Any]] = []
    for symbol in SYMBOLS:
        try:
            quote = None
            if api_key:
                quote = _fetch_finnhub(symbol, api_key)
            if quote is None:
                quote = _fetch_yfinance(symbol)
            if quote:
                quotes.append(quote)
        except Exception as exc:
            log.warning("Quote fetch failed for %s: %s", symbol, exc)
    log.info("Fetched %d equity quotes", len(quotes))
    return quotes
