"""Tarama ayarları. Eşikleri buradan değiştir."""

# --- Sıkışma kutusu (base) ---
MIN_BASE_LEN = 3          # kutudaki en az mum sayısı
MAX_BASE_LEN = 15         # kutudaki en fazla mum sayısı
MAX_HEIGHT_ATR = 2.0      # kutu yüksekliği (gövdeler) / kutu öncesi ATR  -> küçük = sıkı
MAX_HEIGHT_PCT = 12.0     # kutu yüksekliği, fiyatın % si olarak üst sınır
MAX_CONTRACTION = None    # mum boyu küçülme şartı (örn 0.9). None = filtre değil sadece skora etki eder
                          # (BIST'te uzun fitiller yüzünden sert filtre iyi base'leri eliyor)
ATR_LEN = 14

# --- Temas (direnç / destek) ---
MIN_TOUCHES = 2           # direnç seviyesine en az kaç mum çarpıp dönmeli
TOUCH_TOL_ATR = 0.25      # temas toleransı = max(ATR*bu, fiyat*TOUCH_TOL_PCT/100)
TOUCH_TOL_PCT = 0.6

# --- Hacim ---
VOL_SMA = 20              # TradingView'deki Hacim(20, SMA) ile aynı
BREAKOUT_MIN_VOL = 1.0    # kırılım günü hacim / SMA20 en az

# --- Likidite filtresi ---
MIN_PRICE = 1.0
MIN_AVG_TURNOVER_TL = 20_000_000   # son 20 gün ortalama işlem hacmi (TL)

# --- İzleme listesi ---
MAX_DIST_TO_RES_PCT = 4.0  # sıkışmadakiler: dirence en fazla % kaç uzaklıkta olsun
TOP_N_CHARTS = 25          # grafiği çizilecek en iyi aday sayısı

# --- Backtest ---
BT_TARGET_R = 2.0          # hedef = risk x bu (risk = giriş - kutu dibi)
BT_MAX_HOLD = 15           # en fazla kaç gün tut
