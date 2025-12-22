import pandas as pd
from pathlib import Path

# --- Pfad zur Netto-CSV ---
csv_path = Path(r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich\data\netto_angebote_2025-11-23.csv")

# --- CSV laden ---
df = pd.read_csv(csv_path, dtype=str)

# -------------------------------------------------------------
# 1) SPALTENNAMEN NORMALISIEREN  (WICHTIGSTER FIX!)
# -------------------------------------------------------------
df.columns = df.columns.str.strip()

# -------------------------------------------------------------
# 2) DATUMSFELDER NORMALISIEREN (DD.MM.YY → YYYY-MM-DD)
# -------------------------------------------------------------
for col in ["Gueltig_von", "Gueltig_bis"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        df[col] = df[col].dt.strftime("%Y-%m-%d")

# -------------------------------------------------------------
# 3) SPEICHERN (UTF-8 + gleichen Namen behalten)
# -------------------------------------------------------------
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print("✨ Netto-CSV normalisiert & gespeichert:")
print(df.head())
