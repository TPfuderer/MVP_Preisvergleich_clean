from pathlib import Path
import pandas as pd
import re

# -----------------------------
# Pfade
# -----------------------------
IMG_DIR = Path(
    r"/data/images/dd"
)
CSV_PATH = Path(
    r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data\tegut_angebote_2025-12-14.csv"
)

# -----------------------------
# 1) Bilder umbenennen
# -----------------------------
files = sorted(IMG_DIR.glob("lidl_offer_*.jpg"))

mapping = {}  # alt -> neu (nur Dateiname)

for i, old_path in enumerate(files, start=1):
    new_name = f"tegut_offer_{i:02d}.jpg"
    new_path = old_path.with_name(new_name)

    old_path.rename(new_path)
    mapping[old_path.name] = new_name

print(f"✅ {len(mapping)} Bilder umbenannt")

# -----------------------------
# 2) CSV Bildpfade anpassen
# -----------------------------
df = pd.read_csv(CSV_PATH)

def fix_path(p):
    if not isinstance(p, str):
        return p
    for old, new in mapping.items():
        if old in p:
            return re.sub(r"images_tegut/.*$", f"images_tegut/{new}", p)
    return p

df["Bildpfad"] = df["Bildpfad"].apply(fix_path)

df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

print("✅ CSV Bildpfade aktualisiert")
