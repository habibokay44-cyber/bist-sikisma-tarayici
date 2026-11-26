# BIST Sıkışma (Base) Tarayıcı

Fiyatın dar bir kutuya sıkıştığı hisseleri bulur ve kutunun direncini **temas sayısına** göre belirler. Her akşam izleme listesi çıkarır; işleme gün içinde 5/15 dk grafikte sen girersin.

## Ne yapar?

| Ne zaman | Ne yapar |
|---|---|
| Her iş günü 18:35 | Tüm BIST hisselerini günlük mumla tarar → `output/report.md` (tablo + grafikler), `output/results.csv` |
| Elle | Backtest: geçmişteki tüm kırılımların hedef/stop oranları |

## Mantık

1. **Kutu:** Son 3–15 mumun gövdeleri bir kutuya konur. En uzun geçerli kutu seçilir.
   - Kutu yüksekliği ≤ kutu öncesi ATR × 2 ve ≤ fiyatın %12'si (`config.py`).
   - Önceki trendin yönü önemsiz.
2. **Direnç:** Kutu içinde fitillerin/gövdelerin en çok çarpıp döndüğü seviye (tolerans: ATR × 0,25 veya %0,6). En az 2 temas. Destek de aynı mantıkla bulunur.
3. **Durum:**
   - `SIKIŞMA`: hâlâ kutuda, dirence ≤ %4 uzaklıkta. Ertesi gün 5/15 dk'da izle.
   - `KIRILIM`: bugün hem direncin hem kutu tavanının üstünde kapattı.
4. **Skor:** kutu darlığı, mumların küçülmesi, hacmin kuruması (Hacim/SMA20 < 1), temas sayısı, kutu uzunluğu, ana mum (inside bar) sayısı.

Likidite filtresi: fiyat ≥ 1 TL, 20 günlük ortalama işlem hacmi ≥ 20 milyon TL.

## Kurulum (5 dk)

1. GitHub'da yeni bir **private** repo aç, bu klasördeki her şeyi yükle (`.github` klasörü dahil).
2. **Settings → Actions → General → Workflow permissions** → *Read and write permissions* seç.
3. (Opsiyonel) Akşam listesini Telegram'a da göndermek için:
   - Telegram'da @BotFather → `/newbot` → token'ı al.
   - Bota bir mesaj at, sonra `https://api.telegram.org/bot<TOKEN>/getUpdates` adresinden `chat.id`'yi al.
   - **Settings → Secrets and variables → Actions** → `TELEGRAM_TOKEN` ve `TELEGRAM_CHAT_ID` ekle.
4. **Actions** sekmesi → *Günlük sıkışma taraması* → **Run workflow** ile ilk taramayı elle başlat.
5. Sonuç: repodaki `output/report.md` dosyasını aç (grafikler içinde).

## İlk iş: backtest ile ayar yap

**Actions → Backtest → Run workflow** (3y). Bitince *Artifacts* içinden `backtest_trades.csv`'yi indir.
Özet; genel başarı oranını, hacimli/hacimsiz kırılımları, hacim kuruyan/kurumayan kutuları ve temas sayısına göre sonuçları ayrı ayrı gösterir. Buna göre `config.py`'deki eşikleri değiştir.

Backtest varsayımları: giriş = kırılım günü kapanışı, stop = kutu desteği, hedef = 2R, en fazla 15 gün. Aynı gün hem stop hem hedef görülürse stop sayılır. Sen gün içinde daha erken girdiğin için gerçek sonucun farklı olur.

## Bilgisayarda çalıştırma

```bash
pip install -r requirements.txt
python scanner.py                       # tarama
SYMBOLS=ZGYO,EFORC,GENIL python scanner.py   # belirli hisseler
python scanner.py --backtest --period 3y
```

## Bilinmesi gerekenler

- Veri Yahoo Finance'ten (`.IS`) gelir, ücretsizdir. GitHub zamanlı çalıştırmayı birkaç dakika geciktirebilir.
- Hisse listesi TradingView'in açık tarayıcısından otomatik çekilir. Çekilemezse `tickers.txt` kullanılır.
- Yatırım tavsiyesi değildir.
