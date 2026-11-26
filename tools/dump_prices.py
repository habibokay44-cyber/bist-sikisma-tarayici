"""Tüm hisselerin günlük verisini tek dosyaya yazar (ayar/deneme için)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from data import download, get_symbols

data = download(get_symbols(), period="2y")
frames = [df.assign(Symbol=s) for s, df in data.items()]
out = Path(__file__).resolve().parent.parent / "debug"
out.mkdir(exist_ok=True)
pd.concat(frames).rename_axis("Date").reset_index().to_csv(out / "prices.csv.gz", index=False)
print(len(frames), "hisse yazıldı")
