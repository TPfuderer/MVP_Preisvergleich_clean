import os
import re
from collections import Counter
import pandas as pd
from pathlib import Path


# =====================================================
# 1) TOKENIZER
# =====================================================
def tokenize(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9äöüß ]", " ", text)
    return [t for t in text.split() if t.strip()]


# =====================================================
# 2) LOAD SHOPPING LISTS FROM FOLDER
# =====================================================
def load_shopping_history(folder_path):
    folder = Path(folder_path)
    all_tokens = []

    for file in folder.glob("*.*"):
        if file.suffix.lower() in [".txt"]:
            lines = file.read_text(encoding="utf-8").splitlines()
            for l in lines:
                all_tokens.extend(tokenize(l))

        elif file.suffix.lower() in [".csv"]:
            df = pd.read_csv(file)
            # versucht Spalte namens "Produkt", sonst alle Zeilen tokenisieren
            if "Produkt" in df.columns:
                col = df["Produkt"].dropna().tolist()
            else:
                col = df.astype(str).values.flatten().tolist()

            for item in col:
                all_tokens.extend(tokenize(item))

    return Counter(all_tokens)
