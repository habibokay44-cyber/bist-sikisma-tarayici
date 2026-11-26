"""Tarama ayarları. Eşikleri buradan değiştir."""

# --- Sıkışma kutusu (base) ---
MIN_BASE_LEN = 3          # kutudaki en az mum sayısı
MAX_BASE_LEN = 10         # kutudaki en fazla mum sayısı
MAX_HEIGHT_ATR = 2.5      # kutu yüksekliği (fitiller) / kutu öncesi ATR  -> küçük = sıkı
MAX_HEIGHT_PCT = 12.0     # kutu yüksekliği, fiyatın % si olarak üst sınır
MAX_CONTRACTION = None    # mum boyu küçülme şartı (örn 0.9). None = filtre değil sadece skora etki eder
                          # (BIST'te uzun fitiller yüzünden sert filtre iyi base'leri eliyor)
ATR_LEN = 14
PRIOR_BARS = 5            # kutudan önceki kaç muma bakılsın
IMPULSE_BODY_ATR = 0.9    # önceki mumlardan en az biri: gövdesi >= ATR x bu ...
IMPULSE_VOL = 1.2         # ... ve hacmi >= Hacim SMA20 x bu (hacimli itki mumu)
MIN_PRIOR_RANGE = 2.0     # önceki mumların fiyat aralığı / kutu yüksekliği: önce hareket, sonra sıkışma

# --- Temas (direnç / destek) ---
MIN_TOUCHES = 2           # tavana en az kaç fitil değmeli
MIN_SUP_TOUCHES = 2       # tabana en az kaç fitil değmeli (daralan üçgende şart aranmaz)
MAX_WICK_OUTLIERS = 1     # kutudan taşmasına izin verilen fitil sayısı (her yönde, 4+ mumluk kutuda)
MAX_DRIFT = 0.22          # kutu içinde kapanışların kayması / kutu yüksekliği (yataylık)
TOUCH_TOL_ATR = 0.2       # temas toleransı = max(ATR*bu, fiyat*TOUCH_TOL_PCT/100)
TOUCH_TOL_PCT = 0.5

# --- Hacim ---
VOL_SMA = 20              # TradingView'deki Hacim(20, SMA) ile aynı
BREAKOUT_MIN_VOL = 1.0    # kırılım günü hacim / SMA20 en az

# --- Likidite filtresi ---
MIN_PRICE = 1.0
MIN_AVG_TURNOVER_TL = 20_000_000   # son 20 gün ortalama işlem hacmi (TL)

# --- İzleme listesi ---
MAX_DIST_TO_RES_PCT = 4.0  # sıkışmadakiler: dirence en fazla % kaç uzaklıkta olsun
MAX_REPORT_ROWS = 40       # raporda her bölümde en fazla kaç satır
TOP_N_CHARTS = 25          # grafiği çizilecek en iyi aday sayısı

# --- Backtest ---
BT_TARGET_R = 2.0          # hedef = risk x bu (risk = giriş - kutu dibi)
BT_MAX_HOLD = 15           # en fazla kaç gün tut
