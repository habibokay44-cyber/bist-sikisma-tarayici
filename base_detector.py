"""Sıkışma (base) tespiti.

Mantık:
  1. Son N mumun gövdelerini bir kutuya koy (N = 3..15, en uzun geçerli N seçilir).
  2. Kutu, kendinden önceki ATR'ye göre dar olmalı ve mumlar küçülmüş olmalı.
  3. Direnç = kutu içinde fiyatın en çok çarpıp döndüğü seviye (temas sayısı).
     Destek  = aynı mantıkla diplerde.
  4. Kapanış direncin üstündeyse KIRILIM, altındaysa SIKIŞMA (izleme listesi).
Önceki trendin yönü önemsiz.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [df["High"] - df["Low"], (df["High"] - prev_close).abs(), (df["Low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    df["TR"] = tr
    df["ATR"] = tr.ewm(alpha=1 / C.ATR_LEN, adjust=False).mean()  # Wilder
    df["VolSMA"] = df["Volume"].rolling(C.VOL_SMA).mean()
    df["BodyHi"] = df[["Open", "Close"]].max(axis=1)
    df["BodyLo"] = df[["Open", "Close"]].min(axis=1)
    return df


def _edge(values, closes, tol, side, allow_out):
    """Kutunun gerçek tavanı/tabanı.

    Tavan: en düşük seviye öyle ki en fazla `allow_out` fitil bunun üstüne taşmış
    ve hiçbir kapanış üstünde değil. Temas = fitili bu seviyeye tolerans içinde değen mum sayısı.
    """
    order = np.sort(values) if side == "res" else np.sort(values)[::-1]
    for L in order:
        if side == "res":
            if (values > L + tol).sum() > allow_out or (closes > L + tol).any():
                continue
        else:
            if (values < L - tol).sum() > allow_out or (closes < L - tol).any():
                continue
        touches = int((np.abs(values - L) <= tol).sum())
        return float(L), touches
    return None


def find_base(df: pd.DataFrame, end: int) -> dict | None:
    """`end` indeksinde biten en uzun geçerli kutuyu döndürür (df göstergeli olmalı).

    Kutu fitillerle tanımlanır: tavana ve tabana en az MIN_TOUCHES kez değilmiş olmalı,
    kapanışların hepsi içinde kalmalı. Son mum kutudan taşan fitil olamaz
    (hâlâ düşen/yükselen fiyat sıkışma sayılmaz).
    """
    for n in range(C.MAX_BASE_LEN, C.MIN_BASE_LEN - 1, -1):
        s = end - n + 1
        if s - 1 < C.ATR_LEN + 1:
            continue
        w = df.iloc[s : end + 1]
        ref_atr = df["ATR"].iat[s - 1]
        price = df["Close"].iat[end]
        if not np.isfinite(ref_atr) or ref_atr <= 0:
            continue

        tol = max(C.TOUCH_TOL_ATR * ref_atr, price * C.TOUCH_TOL_PCT / 100)
        highs, lows, closes = w["High"].to_numpy(), w["Low"].to_numpy(), w["Close"].to_numpy()
        allow = C.MAX_WICK_OUTLIERS if n >= 4 else 0
        res = _edge(highs, closes, tol, "res", allow)
        sup = _edge(lows, closes, tol, "sup", allow)
        if res is None or sup is None:
            continue
        R, rt = res
        S, st = sup
        # Daralan üçgen: diplerin hepsi yükseliyor, tepeler alçalıyor (GENIL tipi)
        triangle = bool(np.all(np.diff(lows) >= 0) and np.all(np.diff(highs) <= 0))
        if rt < C.MIN_TOUCHES or (st < C.MIN_SUP_TOUCHES and not triangle):
            continue
        # Son mum kutunun dışına fitil atmışsa hâlâ hareket ediyor demektir
        if highs[-1] > R + tol or lows[-1] < S - tol:
            continue

        height = R - S
        height_atr = height / ref_atr
        height_pct = height / price * 100
        if height <= 0 or height_atr > C.MAX_HEIGHT_ATR or height_pct > C.MAX_HEIGHT_PCT:
            continue
        # Önce hareket olmalı: kutudan önceki mumlar kutudan çok daha geniş bir alanda gezmiş
        prior = df.iloc[max(s - C.PRIOR_BARS, 0) : s]
        prior_range = (prior["High"].max() - prior["Low"].min()) / height
        if prior_range < C.MIN_PRIOR_RANGE:
            continue
        # Hacimli itki: önceki mumlardan biri büyük gövdeli ve ortalamanın üstünde hacimli olmalı
        k = max(s - C.PRIOR_BARS - 1, 0)
        p_atr, p_vol = df["ATR"].iat[k], df["VolSMA"].iat[k]
        if not (np.isfinite(p_atr) and np.isfinite(p_vol) and p_vol > 0):
            continue
        body = (prior["Close"] - prior["Open"]).abs()
        impulse = ((body >= C.IMPULSE_BODY_ATR * p_atr) & (prior["Volume"] >= C.IMPULSE_VOL * p_vol)).any()
        if not impulse:
            continue
        # Yataylık: kapanışların ilk ve son yarısının ortalaması arasındaki kayma
        half = max(n // 2, 1)
        drift = abs(closes[-half:].mean() - closes[:half].mean()) / height
        if drift > C.MAX_DRIFT:
            continue
        contraction = w["TR"].mean() / ref_atr
        if C.MAX_CONTRACTION is not None and contraction > C.MAX_CONTRACTION:
            continue

        vol_sma = df["VolSMA"].iat[s - 1]
        vol_ratio = w["Volume"].mean() / vol_sma if vol_sma and np.isfinite(vol_sma) else np.nan
        first = w.iloc[0]
        inside = int(((w["High"].iloc[1:] <= first["High"]) & (w["Low"].iloc[1:] >= first["Low"])).sum())

        return {
            "start": s, "end": end, "length": n,
            "box_top": float(w["BodyHi"].max()), "box_bottom": float(w["BodyLo"].min()),
            "resistance": R, "res_touches": rt, "support": S, "sup_touches": st,
            "height_atr": float(height_atr), "height_pct": float(height_pct), "drift": float(drift), "prior_range": float(prior_range),
            "contraction": float(contraction), "vol_ratio": float(vol_ratio),
            "inside_bars": inside, "ref_atr": float(ref_atr),
        }
    return None


def score(b: dict) -> float:
    tight = 1 - b["height_atr"] / C.MAX_HEIGHT_ATR
    contr = float(np.clip(1 - b["contraction"], -1, 1))
    dry = float(np.clip(1 - b["vol_ratio"], -1, 1)) if np.isfinite(b["vol_ratio"]) else 0.0
    return round(
        35 * tight + 25 * contr + 20 * dry
        + 3 * min(b["res_touches"], 5) + 2 * min(b["sup_touches"], 5) - 15 * b["drift"] + 1.5 * min(b["length"], 10)
        + 2 * min(b["inside_bars"], 5),
        1,
    )


def is_breakout(b: dict, close: float, prev_close: float) -> bool:
    """İlk kırılım: bugün kutu tavanının (direnç) üstünde kapanış, dün içinde."""
    return close > b["resistance"] and prev_close <= b["resistance"]


def scan_symbol(df: pd.DataFrame) -> dict | None:
    """Son mum için sonuç: KIRILIM (bugün direnç üstü kapanış) veya SIKIŞMA (izlemede)."""
    if len(df) < C.ATR_LEN + C.MAX_BASE_LEN + 5:
        return None
    df = add_indicators(df)
    last = len(df) - 1
    close = df["Close"].iat[last]

    # 1) Dün biten kutu + bugün kırılım
    b = find_base(df, last - 1)
    if b and is_breakout(b, close, df["Close"].iat[last - 1]):
        vr = df["Volume"].iat[last] / df["VolSMA"].iat[last - 1]
        b.update(status="KIRILIM", breakout_vol=round(float(vr), 2))
        b["score"] = score(b) + (10 if vr >= C.BREAKOUT_MIN_VOL else -10)
        return _finish(b, df, last)

    # 2) Hâlâ sıkışmada (bugün dahil kutu)
    b = find_base(df, last)
    if b and close <= b["resistance"]:
        dist = max((b["resistance"] / close - 1) * 100, 0.0)
        if dist <= C.MAX_DIST_TO_RES_PCT:
            b.update(status="SIKIŞMA", breakout_vol=np.nan)
            b["score"] = score(b) - dist  # dirence yakın olan önde
            return _finish(b, df, last)
    return None


def _finish(b, df, last):
    close = float(df["Close"].iat[last])
    b["close"] = close
    b["date"] = str(df.index[last].date())
    b["dist_pct"] = round((b["resistance"] / close - 1) * 100, 2)
    b["risk_pct"] = round((b["resistance"] - b["support"]) / b["resistance"] * 100, 2)
    return b


def backtest_symbol(df: pd.DataFrame) -> list[dict]:
    """Geçmişteki her kırılımı bul ve sonucunu ölç.

    Giriş: kırılım günü kapanışı. Stop: kutu desteği. Hedef: risk x BT_TARGET_R.
    Aynı gün hem stop hem hedef görülürse kötümser davranıp stop sayılır.
    """
    df = add_indicators(df)
    out, i = [], C.ATR_LEN + C.MAX_BASE_LEN + 2
    n = len(df)
    while i < n - 1:
        b = find_base(df, i - 1)
        if not (b and is_breakout(b, df["Close"].iat[i], df["Close"].iat[i - 1])):
            i += 1
            continue
        entry = df["Close"].iat[i]
        stop = b["support"]
        risk = entry - stop
        if risk <= 0:
            i += 1
            continue
        target = entry + C.BT_TARGET_R * risk
        result, exit_px, j = "ZAMAN", None, i
        for j in range(i + 1, min(i + 1 + C.BT_MAX_HOLD, n)):
            if df["Low"].iat[j] <= stop:
                result, exit_px = "STOP", stop
                break
            if df["High"].iat[j] >= target:
                result, exit_px = "HEDEF", target
                break
        if exit_px is None:
            exit_px = df["Close"].iat[j]
        vr = df["Volume"].iat[i] / df["VolSMA"].iat[i - 1]
        out.append({
            "date": str(df.index[i].date()), "entry": round(entry, 4), "stop": round(stop, 4),
            "target": round(target, 4), "result": result, "r_mult": round((exit_px - entry) / risk, 2),
            "base_len": b["length"], "touches": b["res_touches"], "height_atr": round(b["height_atr"], 2),
            "vol_ratio": round(b["vol_ratio"], 2), "breakout_vol": round(float(vr), 2), "score": score(b),
        })
        i = j + 1  # işlem bitene kadar yeni sinyal yok
    return out
