import re
import csv
from pathlib import Path


def extract_product_name(line):
    """
    Entfernt ALLE Preis-/Zahl-/EUR-/Pfand-Infos und gibt nur Produktnamen zurück.
    """
    if not line.strip():
        return None

    text = line.strip()

    # 1) Entferne "Pfand ...", z.B. "Pfand 0,25 M"
    text = re.sub(r"\bpfand\b.*$", "", text, flags=re.IGNORECASE)

    # 2) Entferne explizit EUR/€ Angaben
    text = re.sub(r"\b(eur|euro|€)\b", "", text, flags=re.IGNORECASE)

    # 3) Entferne alle Preise am Ende (z.B. "1,29 A", "-0,18", "2.49", "3,99")
    text = re.sub(r"\s*-?\d+[.,]\d{1,2}\s*[A-Za-z]?$", "", text)

    # 4) Entferne Einheiten: "300g", "1kg", "1,5l", "55 g"
    text = re.sub(r"\b\d+[.,]?\d*\s*(g|kg|l|ml)\b", "", text, flags=re.IGNORECASE)

    # 5) Entferne einzelne Zahlen, z.B. "1", "750", "55"
    text = re.sub(r"\b\d+\b", "", text)

    # 6) Doppelte Spaces aufräumen
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else None


def convert_file(input_file):
    p = Path(input_file)
    out_csv = p.with_suffix(".csv")

    rows = []

    with p.open("r", encoding="utf-8") as f:
        for line in f:
            prod = extract_product_name(line)
            if prod:
                rows.append([prod])

    with out_csv.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Produkt"])
        writer.writerows(rows)

    print(f"✔️ Konvertiert → {out_csv}")
    print(f"➡️ Produkte gefunden: {len(rows)}")


if __name__ == "__main__":
    convert_file(
        r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data\einkaufszettel\ausgewertete\liste1"
    )
