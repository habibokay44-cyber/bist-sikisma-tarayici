"""BIST sıkışma (base) tarayıcı.

Kullanım:
  python scanner.py                 # günlük tarama -> output/
  python scanner.py --backtest      # geçmiş kırılımların başarı oranı -> output/backtest_*.csv
  SYMBOLS=ZGYO,EFOR python scanner.py   # sadece belirli hisseler
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import mplfinance as mpf  # noqa: E402
import pandas as pd  # noqa: E402

import config as C  # noqa: E402
import notify  # noqa: E402
from base_detector import backtest_symbol, scan_symbol  # noqa: E402
from data import download, get_symbols  # noqa: E402

OUT = Path(__file__).parent / "output"
CHARTS = OUT / "charts"

TV_STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=mpf.make_marketcolors(up="#26a69a", down="#ef5350", edge="inherit",
                                       wick="inherit", volume={"up": "#26a69a80", "down": "#ef535080"}),
    facecolor="#131722", figcolor="#131722", gridcolor="#2a2e39", gridstyle="-",
)


def liquid(df: pd.DataFrame) -> bool:
    tail = df.tail(20)
    return (tail["Close"].iat[-1] >= C.MIN_PRICE
            and (tail["Close"] * tail["Volume"]).mean() >= C.MIN_AVG_TURNOVER_TL)


def draw_chart(sym: str, df: pd.DataFrame, r: dict) -> str:
    bars = 45
    d = df.tail(bars)
    offset = len(df) - len(d)
    s, e = r["start"] - offset, r["end"] - offset
    vol_sma = df["Volume"].rolling(C.VOL_SMA).mean().tail(bars)
    fig, axes = mpf.plot(
        d, type="candle", style=TV_STYLE, volume=True, returnfig=True, figsize=(9, 6),
        addplot=[mpf.make_addplot(vol_sma, panel=1, color="#2962ff", width=1)],
        title=f"\n{sym}  {r['status']}  kapanış {r['close']:.2f}  direnç {r['resistance']:.2f} "
              f"({r['res_touches']} temas)  destek {r['support']:.2f}",
    )
    ax = axes[0]
    x0 = max(s, 0) - 0.5
    ax.hlines(r["resistance"], x0, len(d) + 1, colors="#2962ff", linewidth=1.4)
    ax.hlines(r["support"], x0, len(d) + 1, colors="#ff9800", linewidth=1.0, linestyles="--")
    if s >= 0:
        ax.add_patch(mpatches.Rectangle((s - 0.5, r["box_bottom"]), e - s + 1,
                                        r["box_top"] - r["box_bottom"],
                                        facecolor="#2962ff22", edgecolor="#2962ff", lw=0.8))
    path = CHARTS / f"{sym}.png"
    fig.savefig(path, dpi=110, bbox_inches="tight", facecolor="#131722")
    matplotlib.pyplot.close(fig)
    return str(path)


def run_scan() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    for old in CHARTS.glob("*.png"):
        old.unlink()
    symbols = get_symbols()
    print(f"{len(symbols)} hisse indiriliyor...")
    data = download(symbols)
    rows, frames = [], {}
    for sym, df in data.items():
        if not liquid(df):
            continue
        r = scan_symbol(df)
        if r:
            r["symbol"] = sym
            rows.append(r)
            frames[sym] = df
    now = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M")
    if not rows:
        (OUT / "report.md").write_text(f"# BIST Sıkışma Taraması — {now}\n\nAday yok.\n")
        print("Aday yok.")
        return

    res = pd.DataFrame(rows).sort_values(["status", "score"], ascending=[True, False])
    cols = ["symbol", "status", "score", "close", "resistance", "res_touches", "support", "dist_pct",
            "risk_pct", "length", "height_atr", "contraction", "vol_ratio", "breakout_vol",
            "inside_bars", "date"]
    res = res[cols].round(3)
    res["score"] = res["score"].round(1)
    res.to_csv(OUT / "results.csv", index=False)

    top = res.head(C.TOP_N_CHARTS)
    for _, row in top.iterrows():
        draw_chart(row["symbol"], frames[row["symbol"]], next(r for r in rows if r["symbol"] == row["symbol"]))

    lines = [f"# BIST Sıkışma Taraması — {now}", ""]
    for status, title in [("KIRILIM", "Bugün kırılım yapanlar"), ("SIKIŞMA", "Sıkışmada (yarın izle)")]:
        part = res[res["status"] == status]
        total = len(part)
        part = part.head(C.MAX_REPORT_ROWS)
        lines += [f"## {title} ({total}, en iyi {len(part)} gösteriliyor — tamamı results.csv'de)", "",
                  "| Hisse | Skor | Kapanış | Direnç (temas) | Destek | Dirence % | Risk % | Mum | Hacim/SMA |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for _, x in part.iterrows():
            vol = x["breakout_vol"] if status == "KIRILIM" else x["vol_ratio"]
            lines.append(f"| {x['symbol']} | {x['score']} | {x['close']:.2f} | {x['resistance']:.2f} "
                         f"({x['res_touches']}) | {x['support']:.2f} | {x['dist_pct']} | {x['risk_pct']} "
                         f"| {x['length']} | {vol:.2f} |")
        lines.append("")
    lines += ["## Grafikler", ""] + [f"![{s}](charts/{s}.png)" for s in top["symbol"]]
    (OUT / "report.md").write_text("\n".join(lines))
    print(res.to_string(index=False))

    if notify.enabled():
        msg = [f"<b>BIST Sıkışma — {now}</b>"]
        for status in ["KIRILIM", "SIKIŞMA"]:
            part = res[res["status"] == status].head(15)
            if len(part):
                msg.append(f"\n<b>{status}</b>")
                msg += [f"{x.symbol}  {x.close:.2f} | R {x.resistance:.2f} ({x.res_touches}) | "
                        f"S {x.support:.2f} | skor {x.score}" for x in part.itertuples()]
        notify.send_text("\n".join(msg))
        for s in top["symbol"].head(8):
            notify.send_photo(str(CHARTS / f"{s}.png"), s)


def run_backtest(period: str) -> None:
    OUT.mkdir(exist_ok=True)
    symbols = get_symbols()
    print(f"{len(symbols)} hisse, {period} geçmiş indiriliyor...")
    data = download(symbols, period=period)
    trades = []
    for sym, df in data.items():
        if len(df) < 60:
            continue
        for t in backtest_symbol(df):
            t["symbol"] = sym
            trades.append(t)
    if not trades:
        print("İşlem bulunamadı.")
        return
    t = pd.DataFrame(trades)
    t.to_csv(OUT / "backtest_trades.csv", index=False)

    def summary(g: pd.DataFrame) -> pd.Series:
        return pd.Series({"işlem": len(g), "hedef_%": round((g.result == "HEDEF").mean() * 100, 1),
                          "stop_%": round((g.result == "STOP").mean() * 100, 1),
                          "kazanan_%": round((g.r_mult > 0).mean() * 100, 1),
                          "ort_R": round(g.r_mult.mean(), 2)})

    print("\n== GENEL ==")
    print(summary(t).to_string())
    t["hacimli_kirilim"] = t.breakout_vol >= C.BREAKOUT_MIN_VOL
    t["hacim_kurudu"] = t.vol_ratio < 1
    t["temas"] = t.touches.clip(upper=4)
    for col in ["hacimli_kirilim", "hacim_kurudu", "temas"]:
        print(f"\n== {col} ==")
        print(t.groupby(col).apply(summary, include_groups=False).to_string())
    print(f"\nDetay: {OUT / 'backtest_trades.csv'}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--backtest", action="store_true")
    p.add_argument("--period", default="3y", help="backtest geçmişi (örn 2y, 5y)")
    a = p.parse_args()
    run_backtest(a.period) if a.backtest else run_scan()
