import pandas as pd
import streamlit as st
from pathlib import Path
import re
import altair as alt
import unicodedata
import json
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# 🔧 funktioniert lokal UND auf Streamlit Cloud
REPO_ROOT = Path(__file__).resolve().parents[2] if "Application" in str(Path(__file__).resolve()) else Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
CSV_IMG_DIR = DATA_DIR / "images" / "images_edeka"
IMAGE_DIR = REPO_ROOT / "images" / "resized"
CSV_IMG_DIR_REWE = DATA_DIR / "images" / "images_rewe"
CSV_IMG_DIR_TEGUT = DATA_DIR / "images" / "images_tegut"
CSV_IMG_DIR_KAUFLAND = DATA_DIR / "images" / "images_kaufland"
CSV_IMG_DIR_NETTO = DATA_DIR / "images" / "images_netto"
CSV_IMG_DIR_MARKTGURU = DATA_DIR / "images" / "images_marktguru"
ALL_CSV_IMG_DIRS = [CSV_IMG_DIR, CSV_IMG_DIR_MARKTGURU, CSV_IMG_DIR_REWE, CSV_IMG_DIR_TEGUT,CSV_IMG_DIR_KAUFLAND, CSV_IMG_DIR_NETTO]




st.title("🛒 MVP Preisvergleich")


st.markdown("""
<style>
/* ================================
   🧱 Produktkarten & Bilder-Layout
   ================================ */

/* Produkt-Karte (optional, falls du .product-card nutzt) */
.product-card {
    border: 1px solid #e5e5e5;
    border-radius: 10px;
    padding: 0.4rem;
    margin-bottom: 1rem;
    background-color: transparent;
}

/* Spalten in st.columns: dürfen in der Höhe mitwachsen */
div[data-testid="stHorizontalBlock"] > div[style*="flex-direction: column"] {
    align-items: stretch !important;
}

/* Bildcontainer: zentriert, aber flexibel in der Höhe */
div[data-testid="stImage"] {
    background-color: white !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;

    /* WICHTIG: keine harte Höhe mehr */
    height: auto !important;
    min-height: 200px !important;      /* Basis-Höhe für Optik */
    max-height: 320px !important;      /* Sicherheitslimit, nicht zu riesig */

    overflow: hidden !important;       /* Kein Überlaufen aus der Box */
    box-shadow: 0 0 6px rgba(0,0,0,0.05);
    margin-bottom: 0.5rem !important;
}

/* Bild selbst: immer komplett sichtbar, skaliert in Box */
div[data-testid="stImage"] img {
    object-fit: contain !important;
    width: 100% !important;
    height: 100% !important;
    max-width: 80% !important;
    max-height: 80% !important;
    border-radius: 0 !important;
    background-color: white !important;
    margin: auto !important;
    display: block !important;
    transform: none !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* 🚫 Unsichtbar machen: leeres .product-card innerhalb Markdown */
div[data-testid="stMarkdownContainer"] > .product-card:empty {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------
# Helpers
# ----------------------------

def short_text(text: str, max_len: int = 60) -> str:
    """Shorten long text and add ellipsis."""
    if not isinstance(text, str):
        return ""
    text = text.strip()
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"

def get_image_for_product(product_name: str) -> str:
    """Zeigt produktspezifische lokale Bilder aus dem 'resized'-Ordner, sonst Platzhalter."""
    base_dir = Path("images/resized")  # ⚡ relativer Pfad (funktioniert lokal + online)
    fallback = base_dir / "fallback.jpg"

    image_map = {
        # --- Markenspezifische ---
        "fulfil protein-riegel": "fulfil protein-riegel.jpg",

        # --- Allgemeine Zuordnungen ---
        "milch": "milch.jpg",
        "vollmilch": "milch.jpg",
        "butter": "butter.jpg",
        "brot": "brot.jpg",
        "quark": "quark.jpg",
        "kaese": "kaese.jpg",
        "käse": "kaese.jpg",
        "joghurt": "joghurt.jpg",
        "apfel": "apfel.jpg",
        "äpfel": "apfel.jpg",
        "banane": "banane.jpg",
        "proteinriegel": "proteinriegel.jpg",
        "protein riegel": "proteinriegel.jpg",
        "protein bar": "proteinriegel.jpg",
        "hackfleisch": "hackfleisch.jpg",
        "hähnchen": "hähnchen.jpg",
        "schinken": "schinken.jpg",
        "mineralwasser": "mineralwasser.jpg",
        "schokolade": "schokolade.jpg",
        "pasta": "pasta.jpg",
        "mehl": "mehl.jpg",
        "pullover": "pullover.jpg",
        "kerze": "kerze.jpg",
        "schmuck": "schmuck.jpg",
        "protein bar deluxe": "protein bar deluxe.jpg",
        "beeren": "beeren.jpg",
        "big block protein-riegel": "big block protein-riegel.jpg",
        "whey": "whey.jpg",
        "buttermilch": "buttermilch.jpg",
        "high protein chocolate pudding": "proteinpudding.jpg",
        "protein pudding": "proteinpudding.jpg",
    }

    # ✅ Längere Keys zuerst, damit spezifische Begriffe Vorrang haben
    image_map = dict(sorted(image_map.items(), key=lambda x: len(x[0]), reverse=True))

    # 🧩 Kein gültiger Name → sofort Fallback
    if not isinstance(product_name, str):
        return fallback.as_posix() if fallback.exists() else \
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/240px-No_image_available.svg"

    # 🔧 Normalisieren
    name = product_name.lower().strip()
    name = name.replace("-", " ").replace("_", " ")

    # 🔍 Bildsuche
    for key, filename in image_map.items():
        key_clean = key.lower().replace("-", " ").replace("_", " ")
        if key_clean in name:
            path = base_dir / filename
            if path.exists():
                return path.as_posix()

    # 🪄 Fallback
    return fallback.as_posix() if fallback.exists() else \
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/240px-No_image_available.svg"


def money_to_float(s: str) -> float | None:
    """Wandelt Preise wie '1,49 €' oder '2.399,00' in float um."""
    if not isinstance(s, str) or not s.strip():
        return None
    s = s.replace("€", "").replace(" ", "")
    if s.count(".") > 1 and s.count(",") == 1:
        s = s.replace(".", "")
    s = s.replace(",", ".")
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    return float(m.group(0)) if m else None

def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))

# ----------------------------
# 📦 Daten laden
# ----------------------------
files = list(DATA_DIR.glob("*.csv"))
dfs = []

for f in files:
    df = pd.read_csv(f, sep=",", quotechar='"', engine="python")
    # --- Retailer anhand Dateinamen bestimmen ---
    name = f.name.lower()
    if "lidl" in name:
        retailer = "Lidl"
    elif "aldi" in name:
        retailer = "Aldi Süd"
    elif "netto" in name:
        retailer = "Netto"
    elif "rewe" in name:
        retailer = "Rewe"
    elif "rossmann" in name:
        retailer = "Rossmann"
    elif "kaufland" in name:
        retailer = "Kaufland"
    elif "amazon" in name:
        retailer = "Amazon"
    elif "edeka" in name:
        retailer = "Edeka"
    elif "tegut" in name:
        retailer = "Tegut"
    elif "store_offers" in name:
        retailer = "Unbekannt"   # ✅ Dein neuer CSV-Name
    else:
        retailer = "Unbekannt"

    df["Retailer"] = retailer

    # --- Spezialfall: Mini-CSV (name + image_path) ---
    if {"name", "image_path"}.issubset(df.columns):
        df.rename(columns={"name": "Produkt", "image_path": "Lokales_Bild"}, inplace=True)
        df["Preis"] = None
        df["Gueltig_von"] = pd.NaT
        df["Gueltig_bis"] = pd.NaT
        df["Marke"] = ""
        dfs.append(df)
        continue

    dfs.append(df)

if not dfs:
    st.warning("Keine CSV-Dateien gefunden.")
    st.stop()

data = pd.concat(dfs, ignore_index=True)


# ----------------------------
# 🌍 GLOBALER DATUMS-SLIDER
# Start = Heute | Lookback = -14 Tage | Max = max(Gueltig_bis)
# ----------------------------
for col in ["Gueltig_von", "Gueltig_bis"]:
    if col in data.columns:
        data[col] = pd.to_datetime(data[col], errors="coerce")

today = pd.Timestamp.today().normalize()
min_limit = today - timedelta(days=14)
max_limit = pd.to_datetime(data["Gueltig_bis"], errors="coerce").max() or today

st.sidebar.markdown("### 🗓️ Angebotszeitraum")
selected_range = st.sidebar.slider(
    "Zeitraum auswählen:",
    min_value=min_limit.to_pydatetime(),
    max_value=max_limit.to_pydatetime(),
    value=(today.to_pydatetime(), today.to_pydatetime()),  # Standard = Heute
    format="DD.MM.YYYY",
)

# 🌍 Hauptdaten (Sliderbereich)
filtered_data = data[
    (data["Gueltig_von"] <= selected_range[1])
    & (data["Gueltig_bis"] >= selected_range[0])
].copy()

# 🌟 Nur heute gültige Angebote (inkl. morgen startende)
filtered_data_current = filtered_data[
    (filtered_data["Gueltig_von"] <= today + pd.Timedelta(days=1))
    & (filtered_data["Gueltig_bis"] >= today)
].copy()


# ➕➕➕ DATUMS-FLAGS (NEU) ─────────────
# Angebot überlappt den gewählten Slider-Zeitraum
data["Ist_im_Slider"] = (
    (data["Gueltig_von"] <= selected_range[1])
    & (data["Gueltig_bis"] >= selected_range[0])
)

data["Ist_aktuell"] = (
    (data["Gueltig_von"] <= today + pd.Timedelta(days=1))
    & (data["Gueltig_bis"] >= today)
)


# ─────────────────────────────────────

st.sidebar.caption(f"📅 Zeitraum: {selected_range[0].date()} – {selected_range[1].date()}")
st.sidebar.caption(f"🔹 Im Zeitraum gültig: {len(filtered_data)} | Heute gültig: {len(filtered_data_current)}")

# ----------------------------
# 🧮 Berechnungen & Bereinigung
# ----------------------------
data = data.drop_duplicates(
    subset=["Produkt", "Marke", "Preis", "Gueltig_von", "Gueltig_bis"],
    keep="first"
).reset_index(drop=True)

# Preisfelder
if "Preis" in data.columns:
    data["Preis_float"] = data["Preis"].apply(money_to_float)
if "Vorheriger Preis" in data.columns:
    data["Vorheriger_float"] = data["Vorheriger Preis"].apply(money_to_float)
if "Preis_kg" in data.columns:
    data["Preis_kg_float"] = data["Preis_kg"].apply(money_to_float)

# Rabattberechnung
if "Vorheriger_float" in data.columns and "Preis_float" in data.columns:
    data["Rabatt_vs_prev"] = (
        (data["Vorheriger_float"] - data["Preis_float"]) / data["Vorheriger_float"]
    ).replace([float("inf"), -float("inf")], None)
else:
    data["Rabatt_vs_prev"] = None

# ----------------------------
# ⚙️ Globale Funktion für Tabs: aktuelle/alle Datenbasis wählen
# ----------------------------
def get_base_data(tab_key: str, default_current: bool = True) -> pd.DataFrame:
    """
    Gibt die Datenbasis für einen Tab zurück:
    - 'Nur aktuelle Angebote' (heute gültig)
    - oder den gesamten Slider-Zeitraum
    """
    use_current = st.toggle(
        "Nur aktuelle Angebote anzeigen",
        value=default_current,
        key=f"use_current_{tab_key}"
    )

    return filtered_data_current if use_current else filtered_data


# ----------------------------
# Sidebar Filter
# ----------------------------
with st.sidebar:
    st.header("Layout")
    cols_per_row = st.slider(
        "Produkte pro Zeile",
        min_value=1,
        max_value=6,
        value=3,
        step=1
    )


# ----------------------------
# Tabs
# ----------------------------

st.markdown("""
    <style>
    div[data-baseweb="tab-list"] {
        overflow-x: auto;
        white-space: nowrap;
    }
    div[data-baseweb="tab"] {
        display: inline-block;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Tabs-Container scrollable und sichtbar halten */
div[data-baseweb="tab-list"] {
    display: flex !important;
    overflow-x: auto !important;
    white-space: nowrap !important;
    scrollbar-width: thin !important;
    padding-bottom: 6px;
}
div[data-baseweb="tab"] {
    flex: 0 0 auto !important;
    white-space: nowrap !important;
    font-size: 15px !important;
    padding: 6px 12px !important;
}
</style>
""", unsafe_allow_html=True)


tab_labels = [
    "🧱 Karten-Ansicht",
    "⭐ Beobachtung & Verlauf",
    "🛒 Einkaufswagen",
    "📈 Preis-Historie"
    "Empfehlungen",
]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

# ---------------------------------------------------
# Tab 1 – Karten-Ansicht
# ---------------------------------------------------
with tab1:
    st.header("🧱 Karten-Ansicht")

    # 🧱 Spaltenanzahl (responsiv)
    cols_per_row = st.sidebar.select_slider(
        "Produkte pro Zeile",
        options=[1, 2, 3, 4, 5, 6, 7, 8],
        value=4,
        help="Passe die Anzahl der Produktspalten an (z. B. 1 auf Handy, 3 auf PC)."
    )

    # --------------------------------------------------
    # 💅 Dynamische CSS-Anpassung
    # --------------------------------------------------
    st.markdown("""
    <style>

    /* =========================================================
       🧱 FIX: Einheitliche Kachelhöhe + sauberer Bild-Container
       ========================================================= */

    /* --- Produktkarte: Fixe Höhe + flexibles Innenlayout --- */
    .product-card {
        display: flex;
        flex-direction: column;
        justify-content: space-between;

        width: 100%;
        height: 380px;  /* 💡 Höhe kannst du 340–420 variieren */

        background-color: #fff;
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        padding: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 0 6px rgba(0,0,0,0.05);

        overflow: hidden; /* verhindert Sprünge */
    }

    /* --- Bildbereich immer gleiche Höhe --- */
    .product-card .image-wrapper {
        height: 180px;      /* 💡 AUCH anpassbar */
        width: 100%;

        display: flex;
        justify-content: center;
        align-items: center;

        margin-bottom: 0.5rem;
    }

    /* --- Bild selbst: niemals zugeschnitten, immer enthalten --- */
    .product-card .image-wrapper img {
        max-width: 100%;
        max-height: 100%;

        object-fit: contain !important;
        margin: auto;
        display: block;
    }

    /* Text & Buttons bleiben unten stabil */
    .product-card .content-area {
        flex-grow: 1;
        width: 100%;
    }
    
    .product-title {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
    max-width: 100%;
    cursor: pointer;
}

.product-price {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.95rem;
    margin-bottom: 0.2rem;
    max-width: 100%;
}

.product-ppkg {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.8rem;
    color: #666;
    margin-bottom: 0.3rem;
    max-width: 100%;
}

.product-brand {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    font-size: 0.8rem;
    color: #666;
}



    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 🛒 Einkaufswagen initialisieren
    # --------------------------------------------------
    if "cart" not in st.session_state:
        st.session_state.cart = []

    # --------------------------------------------------
    # 🔍 Such- und Filteroptionen
    # --------------------------------------------------
    search_term = st.text_input(
        "Produkte suchen (z. B. Butter, Milch, Joghurt)",
        placeholder="Produktname eingeben …"
    ).strip().lower()

    retailers = sorted(data["Retailer"].dropna().unique())
    selected_retailers = st.multiselect(
        "Händler filtern:",
        retailers,
        default=[r for r in retailers if r in ["Rewe", "Edeka", "Kaufland"]]
    )
    use_current = st.toggle("Nur aktuelle Angebote anzeigen", value=True, key="filter_current_tab5")

    subset = data[data["Retailer"].isin(selected_retailers)].copy()
    if use_current:
        subset = subset[subset["Ist_aktuell"]]

    if search_term:
        subset = subset[
            subset["Produkt"].str.lower().str.contains(search_term, na=False)
            | subset["Marke"].str.lower().str.contains(search_term, na=False)
        ]

    # --------------------------------------------------
    # 💶 Sortierung
    # --------------------------------------------------
    if "Preis_float" not in subset.columns:
        subset["Preis_float"] = subset["Preis"].apply(money_to_float)

    sort_option = st.selectbox(
        "Sortieren nach:",
        [
            "Kein Sortieren",
            "Preis pro kg/l (aufsteigend)",
            "Preis (aufsteigend)",
            "Preis (absteigend)",
            "Rabatt (absteigend)"
        ]
    )
    if sort_option == "Preis (aufsteigend)":
        subset = subset.sort_values("Preis_float", ascending=True)
    elif sort_option == "Preis pro kg/l (aufsteigend)":
        subset = subset.sort_values("Preis_kg_float", ascending=True, na_position="last")
    elif sort_option == "Preis (absteigend)":
        subset = subset.sort_values("Preis_float", ascending=False)
    elif sort_option == "Rabatt (absteigend)" and "Rabatt_vs_prev" in subset.columns:
        subset = subset.sort_values("Rabatt_vs_prev", ascending=False)


    # --------------------------------------------------
    # 🔢 Pagination / „Mehr anzeigen“
    # --------------------------------------------------
    if "card_limit" not in st.session_state:
        st.session_state.card_limit = 50
    shown_subset = subset.head(st.session_state.card_limit)

    # --------------------------------------------------
    # 🧱 Produktanzeige
    # --------------------------------------------------
    if shown_subset.empty:
        st.info("Keine passenden Produkte gefunden.")
    else:
        cols = st.columns(cols_per_row)

        for i, (_, row) in enumerate(shown_subset.iterrows()):
            with cols[i % cols_per_row]:
                st.markdown("<div class='product-card'>", unsafe_allow_html=True)

                # === Bildanzeige ===
                csv_image = row.get("Bildpfad")
                if isinstance(csv_image, str) and csv_image.strip():
                    img_candidate = Path(csv_image)
                    if img_candidate.exists():
                        st.image(img_candidate.as_posix(), use_container_width=True)
                    else:
                        else_found = False
                        for img_dir in ALL_CSV_IMG_DIRS:
                            candidate_path = img_dir / img_candidate.name
                            if candidate_path.exists():
                                st.image(candidate_path.as_posix(), use_container_width=True)
                                else_found = True
                                break
                        if not else_found and (IMAGE_DIR / img_candidate.name).exists():
                            st.image((IMAGE_DIR / img_candidate.name).as_posix(), use_container_width=True)
                        elif not else_found:
                            st.image(get_image_for_product(row["Produkt"]), use_container_width=True)
                else:
                    st.image(get_image_for_product(row["Produkt"]), use_container_width=True)

                # === Produktinfos ===
                full_name = str(row.get("Produkt", ""))
                short_name = short_text(full_name, 60)

                st.markdown(
                    f"<div class='product-title' title='{full_name}'>{short_name}</div>",
                    unsafe_allow_html=True
                )

                # 🔽 GENAU HIER EINFÜGEN
                if len(full_name) > 60:
                    with st.expander("Vollständiger Produktname"):
                        st.write(full_name)
                # 🔼 GENAU HIER

                brand_line = f"{row.get('Marke', '')} – {row['Retailer']}"

                st.markdown(
                    f"<div class='product-brand'>{brand_line}</div>",
                    unsafe_allow_html=True
                )
                # Preis → eigene Zeile
                price_display = f"💶 <b>{row['Preis']}</b>"
                st.markdown(
                    f"<div class='product-price'>{price_display}</div>",
                    unsafe_allow_html=True
                )

                # Preis pro kg/L → eigene Zeile
                ppkg = row.get("Preis_kg", "")
                if ppkg:
                    st.markdown(
                        f"<div class='product-ppkg'>{ppkg}</div>",
                        unsafe_allow_html=True
                    )

                von = pd.to_datetime(row.get("Gueltig_von"), errors="coerce")
                bis = pd.to_datetime(row.get("Gueltig_bis"), errors="coerce")
                if pd.notna(von) and pd.notna(bis):
                    st.write(f"🗓️ {von:%d.%m.%Y} – {bis:%d.%m.%Y}")

                r = row.get("Rabatt_vs_prev")
                if pd.notna(r) and r > 0:
                    st.markdown(f"<span style='color:green'>💸 Rabatt: {(r * 100):.1f}%</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:gray'>🏷️ Aktion / Kein Rabatt</span>", unsafe_allow_html=True)

                # === Warenkorb-Button ===
                widget_key = f"add_btn_{row.name}_{i}"
                state_key = f"add_state_{row.name}_{i}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = False
                button_label = "➖ Entfernen" if st.session_state[state_key] else "➕ Hinzufügen"

                if st.button(button_label, key=widget_key):
                    if st.session_state[state_key]:
                        st.session_state.cart = [
                            item for item in st.session_state.cart
                            if not (item.get("Produkt") == row["Produkt"]
                                    and item.get("Retailer") == row["Retailer"])
                        ]
                        st.session_state[state_key] = False
                    else:
                        st.session_state.cart.append(row.to_dict())
                        st.session_state[state_key] = True
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

        # 🔽 Mehr/Weniger anzeigen
        if len(subset) > st.session_state.card_limit:
            if st.button("🔽 Mehr anzeigen"):
                st.session_state.card_limit += 40
                st.rerun()
        elif len(subset) > 12:
            if st.button("🔼 Weniger anzeigen"):
                st.session_state.card_limit = 40
                st.rerun()

    st.divider()

    # --------------------------------------------------
    # 🛒 Einkaufswagen-Vorschau
    # --------------------------------------------------
    if st.session_state.cart:
        st.markdown("### 🛒 Aktueller Einkaufswagen")
        st.dataframe(
            pd.DataFrame(st.session_state.cart)[["Retailer", "Produkt", "Preis"]],
            use_container_width=True
        )

# ---------------------------------------------------
# Tab 2 – Beobachtung & Verlauf (vormals Tab7)
# ---------------------------------------------------
with tab2:
    st.header("⭐ Beobachtung & Verlauf (Favoriten)")

    fav_file = Path(r"C:\Users\pfudi\PycharmProjects\PythonProject\Application\favourites.json")

    # 🔹 Datei ggf. mit Beispieldaten anlegen
    if not fav_file.exists():
        default_data = {
            "favourites": ["ESN Designer Bar", "Milbona Skyr", "Whey Protein", "Volvic Wasser"],
            "favourite_brands": ["ESN", "Ehrmann", "Müller", "Alpro"]
        }
        fav_file.write_text(json.dumps(default_data, indent=4, ensure_ascii=False))

    fav_data = json.loads(fav_file.read_text(encoding="utf-8"))
    favourites = fav_data.get("favourites", [])
    favourite_brands = fav_data.get("favourite_brands", [])

    if "cart" not in st.session_state:
        st.session_state.cart = []

    st.divider()
    st.subheader("🍫 Beobachtete Produktkategorien")

    favourite_categories = fav_data.get("favourite_categories", [])
    if not isinstance(favourite_categories, list):
        favourite_categories = [favourite_categories] if favourite_categories else []

    selected_cats = st.multiselect(
        "Kategorien filtern (leer = alle anzeigen)",
        options=favourite_categories,
        default=favourite_categories,
        key="fav_filter_categories"
    )
    active_cats = selected_cats if selected_cats else favourite_categories

    if active_cats:
        def normalize_simple(s):
            if not isinstance(s, str):
                return ""
            s = s.lower()
            s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
            s = re.sub(r"[\s\-_/]+", "", s)
            return s

        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        date_mask = data["Ist_aktuell"]

        subset_list = []
        for cat in active_cats:
            cat_mask = (
                    data["Produkt"].apply(lambda x: normalize_simple(cat) in normalize_simple(str(x))) |
                    data["Marke"].apply(lambda x: normalize_simple(cat) in normalize_simple(str(x)))
            )
            subset_list.append(data[date_mask & cat_mask])

        subset_cats = (
            pd.concat(subset_list, ignore_index=True)
            .drop_duplicates(subset=["Produkt", "Retailer", "Preis"])
        )

        if subset_cats.empty:
            st.info("Keine aktuellen oder ab morgen gültigen Angebote zu den beobachteten Kategorien gefunden.")
        else:
            subset_cats = subset_cats.sort_values("Preis_float", ascending=True).reset_index(drop=True).head(12)
            cols_c = st.columns(3)

            for i, (_, row) in enumerate(subset_cats.iterrows()):
                with cols_c[i % 3]:
                    st.image(get_image_for_product(row["Produkt"]), use_container_width=True)
                    full_name = str(row.get("Produkt", ""))
                    short_name = short_text(full_name, 60)

                    if len(full_name) > 60:
                        with st.expander(short_name):
                            st.markdown(f"**{full_name}**")
                    else:
                        st.markdown(f"**{full_name}**")

                    st.caption(f"{row.get('Marke', '')} – {row['Retailer']}")
                    st.write(f"💶 **{row['Preis']}** ({row.get('Preis_kg', '')})")

                    if "Gueltig_von" in row and "Gueltig_bis" in row:
                        von = pd.to_datetime(row["Gueltig_von"], errors="coerce")
                        bis = pd.to_datetime(row["Gueltig_bis"], errors="coerce")
                        if pd.notna(von) and pd.notna(bis):
                            st.write(f"🗓️ {von:%d.%m.%Y} – {bis:%d.%m.%Y}")

                    r = row.get("Rabatt_vs_prev")
                    if pd.notna(r) and r > 0:
                        st.markdown(
                            f"<span style='color:green'>💸 Rabatt: {(r * 100):.1f}%</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown("<span style='color:gray'>🏷️ Aktion / Kein Rabatt</span>", unsafe_allow_html=True)

                    if st.button("➕ Hinzufügen", key=f"cat_add_{i}"):
                        st.session_state.cart.append(row.to_dict())
                        st.success(f"✅ {row['Produkt']} hinzugefügt!")
                        st.rerun()
    else:
        st.info("Noch keine beobachteten Kategorien hinterlegt.")

    if st.session_state.get("cart"):
        st.divider()
        st.markdown("### 🛒 Aktueller Einkaufswagen")
        st.dataframe(
            pd.DataFrame(st.session_state.cart)[["Retailer", "Produkt", "Preis"]],
            use_container_width=True
        )

# ---------------------------------------------------
# Tab 3 – Einkaufswagen (vormals Tab4)
# ---------------------------------------------------
with tab3:
    st.subheader("🛒 Deine Einkaufsliste")

    if "cart" not in st.session_state:
        st.session_state.cart = []

    if not st.session_state.cart:
        st.info("Noch keine Produkte im Einkaufswagen.")
    else:
        cart_df = pd.DataFrame(st.session_state.cart)

        st.dataframe(
            cart_df[["Retailer", "Produkt", "Marke", "Preis", "Preis_kg"]],
            use_container_width=True
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Ausgewählte entfernen (noch nicht implementiert)"):
                st.warning("Manuelles Entfernen folgt später.")
        with col2:
            if st.button("🧹 Warenkorb leeren"):
                st.session_state.cart = []
                st.success("Warenkorb geleert.")

# ---------------------------------------------------
# Tab 4 – Preis-Historie (vormals Tab3)
# ---------------------------------------------------
with tab4:
    st.subheader("📉 Preis-Historie durchsuchen")

    search_hist = st.text_input(
        "Produkt oder Stichwort eingeben (z. B. 'Butter', 'Quark', 'Milch')",
        placeholder="z. B. Butter"
    )

    if search_hist:
        s = normalize_text(search_hist)
        pattern = rf"\b{s}\b"

        matches = data[
            data["Produkt"].apply(lambda x: bool(re.search(pattern, normalize_text(str(x))))) |
            data["Marke"].apply(lambda x: bool(re.search(pattern, normalize_text(str(x)))))
        ].copy()

        if matches.empty:
            matches = data[
                data["Produkt"].apply(lambda x: s in normalize_text(str(x))) |
                data["Marke"].apply(lambda x: s in normalize_text(str(x)))
            ].copy()

        if not matches.empty:
            st.success(f"{len(matches)} passende Angebote gefunden.")

            matches["Gueltig_von"] = pd.to_datetime(matches["Gueltig_von"], errors="coerce")
            matches = matches.dropna(subset=["Gueltig_von", "Preis_float"])

            chart = (
                alt.Chart(matches)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Gueltig_von:T", title="Gültig ab"),
                    y=alt.Y("Preis_float:Q", title="Preis (€)"),
                    color="Retailer:N",
                    tooltip=["Produkt", "Marke", "Retailer", "Preis", "Gueltig_von", "Gueltig_bis"]
                )
                .properties(width=800, height=400)
            )
            st.altair_chart(chart, use_container_width=True)

            st.dataframe(
                matches[["Retailer", "Produkt", "Marke", "Preis", "Gueltig_von", "Gueltig_bis"]],
                use_container_width=True
            )
        else:
            st.warning("Keine Produkte gefunden, die auf deine Suche passen.")
    else:
        st.info("Bitte gib ein Stichwort ein, um Preisverläufe zu sehen.")

# ---------------------------------------------------
# Tab 5 – Empfehlungen (aus gespeicherten CSVs)
# ---------------------------------------------------
with st.tab("⭐ Empfehlungen"):
    st.header("🔮 Week 1 Empfehlungen (vorgefertigt)")

    # Ordner mit deinen Recommendation-CSVs
    reco_folder = Path(
        r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data\user_recommendations\week1"
    )

    reco_files = list(reco_folder.glob("*.csv"))

    if not reco_files:
        st.warning("Keine Empfehlungsdateien in week1 gefunden.")
        st.stop()

    # Alle CSVs laden und zusammenführen
    reco_dfs = []
    for f in reco_files:
        try:
            df = pd.read_csv(f)
            df["Quelle"] = f.name
            reco_dfs.append(df)
        except Exception as e:
            st.error(f"Fehler beim Laden von {f.name}: {e}")

    if not reco_dfs:
        st.warning("Konnte keine Empfehlungstabellen laden.")
        st.stop()

    reco = pd.concat(reco_dfs, ignore_index=True)

    # Score vorhanden → sortieren
    if "Score" in reco.columns:
        reco = reco.sort_values("Score", ascending=False).reset_index(drop=True)
    else:
        st.error("Score fehlt in den gespeicherten week1-Empfehlungen!")
        st.stop()

    st.success(f"📦 {len(reco)} Empfehlungen geladen (Week 1)")

    # ---- Anzeige wie in Tab 1 ----
    cols = st.columns(cols_per_row)

    for i, (_, row) in enumerate(reco.iterrows()):
        with cols[i % cols_per_row]:
            st.markdown("<div class='product-card'>", unsafe_allow_html=True)

            # === Bild ===
            st.image(get_image_for_product(row.get("Produkt", "")), use_container_width=True)

            # === Produktname ===
            full_name = str(row.get("Produkt", ""))
            short_name = short_text(full_name, 60)

            st.markdown(
                f"<div class='product-title' title='{full_name}'>{short_name}</div>",
                unsafe_allow_html=True
            )

            # Optional Volltext
            if len(full_name) > 60:
                with st.expander("Vollständiger Produktname"):
                    st.write(full_name)

            # Marke + Händler
            brand_line = f"{row.get('Marke', '')} – {row.get('Retailer', 'Unbekannt')}"
            st.markdown(f"<div class='product-brand'>{brand_line}</div>", unsafe_allow_html=True)

            # Preis
            st.markdown(
                f"<div class='product-price'><b>{row.get('Preis', '')}</b></div>",
                unsafe_allow_html=True
            )

            # Score anzeigen
            st.caption(f"🔢 Score: {row.get('Score', 0)}")

            # === Datum (falls vorhanden) ===
            von = pd.to_datetime(row.get("Gueltig_von"), errors="coerce")
            bis = pd.to_datetime(row.get("Gueltig_bis"), errors="coerce")
            if pd.notna(von) and pd.notna(bis):
                st.write(f"🗓️ {von:%d.%m.%Y} – {bis:%d.%m.%Y}")

            st.markdown("</div>", unsafe_allow_html=True)
