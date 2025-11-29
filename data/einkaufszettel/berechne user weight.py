import pandas as pd
import re
from collections import Counter
from pathlib import Path

# =========================================================
# TOKENIZER
# =========================================================
def tokenize(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9äöüß ]", " ", text)
    return [t for t in text.split() if t.strip()]


# =========================================================
# USER PROFILE FROM EINKAUFSZETTEL CSV
# =========================================================
def build_user_profile(csv_path):
    df = pd.read_csv(csv_path)
    tokens = []
    for p in df["Produkt"]:
        tokens.extend(tokenize(p))
    return Counter(tokens)


# =========================================================
# PRODUCT SCORING – Marke + Produkt kombiniert
# =========================================================
def score_product_combined(row, user_profile):
    combined_text = f"{row['Marke']} {row['Produkt']}"
    tokens = tokenize(combined_text)
    return sum(user_profile.get(t, 0) for t in tokens)


# =========================================================
# RECOMMEND PRODUCTS FROM A FLYER CSV
# =========================================================
def recommend_from_flyer(flyer_csv_path, user_profile):
    df = pd.read_csv(flyer_csv_path)

    if "Marke" not in df.columns or "Produkt" not in df.columns:
        print(f"❌ Spalten 'Marke' oder 'Produkt' fehlen in {flyer_csv_path}")
        return None

    df["Score"] = df.apply(
        lambda row: score_product_combined(row, user_profile),
        axis=1
    )

    return df.sort_values("Score", ascending=False)


# =========================================================
# MAIN PIPELINE – SPEICHERT ALLES IN EXTRA ORDNER
# =========================================================
if __name__ == "__main__":

    # -------------------------------------------
    # 1) Load user profile (Week 1)
    # -------------------------------------------
    user_profile = build_user_profile(
        r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data\einkaufszettel\ausgewertete\liste1.csv"
    )

    print("============================================")
    print(" USER PROFILE WEEK 1")
    print("============================================")
    print(user_profile)
    print()

    # -------------------------------------------
    # 2) Create output folder for week1
    # -------------------------------------------
    output_folder = Path(
        r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data\user_recommendations\week1"
    )
    output_folder.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------
    # 3) Load ALL flyer CSVs in /data/
    # -------------------------------------------
    flyer_root = Path(r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data")
    flyer_files = list(flyer_root.glob("*.csv"))

    if not flyer_files:
        print("❌ Keine Flyer-CSVs gefunden.")
        exit()

    # -------------------------------------------
    # 4) Score each flyer + SAVE IN EXTRA FOLDER
    # -------------------------------------------
    for flyer in flyer_files:
        print("\n====================================================")
        print(f" EMPFEHLUNGEN FÜR FLYER: {flyer.name}")
        print("====================================================")

        recs = recommend_from_flyer(flyer, user_profile)

        if recs is not None:
            # Ausgabe der Top 20 im Terminal
            print(recs[["Marke", "Produkt", "Score"]].head(20).to_string(index=False))

            # ---- SAVE FILE IN WEEK 1 FOLDER ----
            out_path = output_folder / f"week1_{flyer.stem}.csv"
            recs.to_csv(out_path, index=False, encoding="utf-8")

            print(f"💾 Gespeichert in: {out_path}")
