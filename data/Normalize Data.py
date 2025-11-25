import pandas as pd
from pathlib import Path
import re

DATA_DIR = Path(r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data")

csv_files = list(DATA_DIR.glob("*.csv"))

def normalize_price(value):
    if pd.isna(value):
        return value

    val = str(value).strip()

    # Alles außer Ziffern, Punkt, Komma entfernen
    val = re.sub(r"[^0-9\.,]", "", val)

    # Punkt durch Komma ersetzen
    val = val.replace(".", ",")

    # Falls kein Komma → zwei Nachkommastellen anhängen
    if "," not in val:
        val = f"{val},00"

    # Falls Komma ohne Nachkommastellen → "X,00"
    if re.match(r"^\d+,$", val):
        val = val + "00"

    # Falls mehr als 2 Nachkommastellen → nur die ersten beiden behalten
    parts = val.split(",")
    if len(parts) == 2 and len(parts[1]) > 2:
        val = parts[0] + "," + parts[1][:2]

    return f"€ {val}"


for file in csv_files:
    print(f"📄 Normalisiere: {file.name}")

    df = pd.read_csv(file)

    # --- Regel 1: Marke ---
    if "Marke" in df.columns:
        df["Marke"] = df["Marke"].replace("", "Keine Marke").fillna("Keine Marke")

    # --- Regel 2: Vorheriger Preis leer ---
    if "Vorheriger Preis" in df.columns:
        df["Vorheriger Preis"] = (
            df["Vorheriger Preis"]
            .replace("", "Kein vorheriger Preis")
            .fillna("Kein vorheriger Preis")
        )

    # --- Regel 3: Preis_kg leer ---
    if "Preis_kg" in df.columns:
        df["Preis_kg"] = (
            df["Preis_kg"]
            .replace("", "Kein Mengenpreis")
            .fillna("Kein Mengenpreis")
        )

    # --- Regel 4: Preis normalisieren ---
    if "Preis" in df.columns:
        df["Preis"] = df["Preis"].apply(normalize_price)

    # --- Regel 5: Vorheriger Preis normalisieren ---
    if "Vorheriger Preis" in df.columns:
        def norm_prev(v):
            if isinstance(v, str) and "Kein vorheriger Preis" in v:
                return v
            return normalize_price(v)

        df["Vorheriger Preis"] = df["Vorheriger Preis"].apply(norm_prev)

    # Speichern
    df.to_csv(file, index=False, encoding="utf-8-sig")

print("✅ Alle CSVs erfolgreich normalisiert.")
