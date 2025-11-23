import pandas as pd
from pathlib import Path

# --- Pfad zur Datei ---
csv_path = Path(r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich\data\netto_angebote_2025-11-23.csv")

# --- CSV laden ---
df = pd.read_csv(csv_path, dtype=str)

# --- Datumsfelder bereinigen ---
# Netto liefert DD.MM.YY → in datetime umwandeln
df["Gueltig_von"] = pd.to_datetime(df["Gueltig_von"], dayfirst=True, errors="coerce")
df["Gueltig_bis"] = pd.to_datetime(df["Gueltig_bis"], dayfirst=True, errors="coerce")

# --- Als ISO-Format exportieren (YYYY-MM-DD) ---
df["Gueltig_von"] = df["Gueltig_von"].dt.strftime("%Y-%m-%d")
df["Gueltig_bis"] = df["Gueltig_bis"].dt.strftime("%Y-%m-%d")

# --- Speichern: gleiche Datei überschreiben ---
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print("✨ Netto-Datumsfelder bereinigt und gespeichert!")
print(df[["Gueltig_von", "Gueltig_bis"]].head())
