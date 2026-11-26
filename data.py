"""Hisse listesi ve fiyat verisi (Yahoo Finance, .IS uzantılı)."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).parent


def get_symbols() -> list[str]:
    """Önce TradingView tarayıcısından tüm BIST hisselerini çek, olmazsa tickers.txt."""
    if os.getenv("SYMBOLS"):  # elle: SYMBOLS="ZGYO,EFOR"
        return [s.strip().upper() for s in os.environ["SYMBOLS"].split(",") if s.strip()]
    try:
        r = requests.post(
            "https://scanner.tradingview.com/turkey/scan",
            json={
                "filter": [
                    {"left": "exchange", "operation": "equal", "right": "BIST"},
                    {"left": "type", "operation": "equal", "right": "stock"},
                ],
                "columns": ["name"],
                "range": [0, 2000],
            },
            timeout=20,
        )
        r.raise_for_status()
        syms = sorted({row["d"][0] for row in r.json()["data"] if row["d"][0].isalnum()})
        if len(syms) > 100:
            return syms
    except Exception as e:  # noqa: BLE001
        print(f"[uyarı] TradingView listesi alınamadı ({e}), tickers.txt kullanılıyor")
    txt = (ROOT / "tickers.txt").read_text().split()
    return sorted({t.strip().upper() for t in txt if t.strip() and not t.startswith("#")})


def download(symbols: list[str], period: str = "1y", interval: str = "1d") -> dict[str, pd.DataFrame]:
    """{SEMBOL: OHLCV DataFrame} döndürür. Boş/eksik veriler atlanır."""
    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(symbols), 100):
        chunk = symbols[i : i + 100]
        raw = yf.download(
            [f"{s}.IS" for s in chunk], period=period, interval=interval,
            group_by="ticker", auto_adjust=False, threads=True, progress=False,
        )
        for s in chunk:
            try:
                df = raw[f"{s}.IS"] if isinstance(raw.columns, pd.MultiIndex) else raw
                df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
                df = df[df["Volume"] > 0]
                if len(df) > 0:
                    out[s] = df
            except KeyError:
                continue
    return out
