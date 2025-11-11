import pandas as pd
import streamlit as st
from pathlib import Path
import re
import altair as alt
import unicodedata
import json
from datetime import datetime, timedelta
from PIL import Image
from pandas import Timedelta


# 🔧 funktioniert lokal UND auf Streamlit Cloud
REPO_ROOT = Path(__file__).resolve().parents[2] if "Application" in str(Path(__file__).resolve()) else Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
CSV_IMG_DIR = DATA_DIR / "images" / "images_edeka"
IMAGE_DIR = REPO_ROOT / "images" / "resized"


st.title("🛒 MVP Preisvergleich")

st.markdown("""
<style>
/* --- Einheitliche Produkt-Kachel --- */
.product-card {
    border: 1px solid #e5e5e5;
    border-radius: 10px;
    padding: 0.4rem;
    margin-bottom: 1rem;
    background-color: transparent;
}

/* --- Einheitliche Bildbox: Weißer Hintergrund + zentriert --- */
div[data-testid="stImage"] {
    background-color: white !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;       /* vertikal zentrieren */
    justify-content: center !important;   /* horizontal zentrieren */
    height: 180px !important;
    overflow: hidden !important;
    box-shadow: 0 0 6px rgba(0,0,0,0.05);
}

/* --- Bild: NIE skalieren oder zuschneiden --- */
div[data-testid="stImage"] img {
    object-fit: contain !important;
    width: auto !important;
    height: auto !important;
    max-width: 80% !important;           /* 🧩 kein Zwangszoom */
    max-height: 80% !important;          /* 🧩 etwas Innenabstand */
    border-radius: 0 !important;
    background-color: white !important;
    margin: auto !important;
    display: block !important;
    transform: none !important;          /* kein Zoom-Effekt */
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

# 🌟 Nur heute gültige Angebote
filtered_data_current = filtered_data[
    (filtered_data["Gueltig_von"] <= today)
    & (filtered_data["Gueltig_bis"] >= today)
].copy()

# ➕➕➕ DATUMS-FLAGS (NEU) ─────────────
# Angebot überlappt den gewählten Slider-Zeitraum
data["Ist_im_Slider"] = (
    (data["Gueltig_von"] <= selected_range[1])
    & (data["Gueltig_bis"] >= selected_range[0])
)

# Angebot ist HEUTE gültig
data["Ist_heute"] = (
    (data["Gueltig_von"] <= today)
    & (data["Gueltig_bis"] >= today)
)

# Kompatibilität: 'Ist_aktuell' = heute gültig (bestehende Filter/Tabs nutzen das)
data["Ist_aktuell"] = data["Ist_heute"]
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
    st.header("Filter")
    retailers = st.multiselect("Retailer", sorted(data["Retailer"].unique()), default=sorted(data["Retailer"].unique()))
    search = st.text_input("Suche nach Produkt oder Marke (z.B. 'Butter' findet auch 'Süßrahmbutter')")
    only_online = st.checkbox("Nur Online verfügbar", value=False)
    max_rows = st.slider("Anzahl Zeilen anzeigen", 50, 1000, 200, step=50)

# Filter anwenden (nur aktuelle Angebote)
mask = data["Retailer"].isin(retailers) & data["Ist_aktuell"]

if search:
    s = normalize_text(search)
    mask &= (
        data["Produkt"].apply(lambda x: s in normalize_text(str(x))) |
        data["Marke"].apply(lambda x: s in normalize_text(str(x)))
    )

if only_online and "Nur_online" in data.columns:
    mask &= data["Nur_online"].str.lower() == "ja"

filtered = data[mask].copy()

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
    "📈 Preis-Historie",
    "🔥 Top 15 Rabatte"
]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

# ---------------------------------------------------
# Tab 1 – Karten-Ansicht (vormals Tab5)
# ---------------------------------------------------
with tab1:
    st.header("Karten-Ansicht")

    # 🧱 Spaltenanzahl für Produktkarten (mobilfreundlich)
    cols_per_row = st.sidebar.select_slider(
        "Produkte pro Zeile",
        options=[1, 2, 3],
        value=3,
        help="Passe die Anzahl der Produktspalten an (z. B. 1 auf Handy, 3 auf PC)."
    )

    # 🔧 Bildhöhe dynamisch an Spaltenzahl anpassen
    if cols_per_row == 1:
        img_height = 220
    elif cols_per_row == 2:
        img_height = 190
    else:
        img_height = 170

    st.markdown(f"""
    <style>
    div[data-testid="stImage"] {{
        height: {img_height}px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # 🛒 Einkaufswagen initialisieren
    if "cart" not in st.session_state:
        st.session_state.cart = []

    # 🔍 Suchfeld
    search_term = st.text_input(
        "Produkte suchen (z. B. Butter, Milch, Joghurt)",
        placeholder="Produktname eingeben …"
    ).strip().lower()

    # Sofortige Vorschläge beim Tippen
    if search_term and len(search_term) >= 2:
        all_names = pd.concat([
            data["Produkt"].dropna().astype(str),
            data.get("Marke", pd.Series(dtype=str)).dropna().astype(str)
        ]).unique()
        suggestions = [name for name in all_names if search_term in name.lower()][:5]

    # 🏪 Händler-Filter
    retailers = sorted(data["Retailer"].dropna().unique())
    selected_retailers = st.multiselect(
        "Händler filtern:",
        retailers,
        default=retailers
    )

    # 🧭 Filter: nur aktuelle oder alle anzeigen
    use_current = st.toggle("Nur aktuelle Angebote anzeigen", value=True, key="filter_current_tab5")

    if use_current:
        subset = data[data["Ist_aktuell"] & data["Retailer"].isin(selected_retailers)].copy()
    else:
        subset = data[data["Retailer"].isin(selected_retailers)].copy()

    # 🔎 Suchfeld anwenden
    if search_term:
        subset = subset[
            subset["Produkt"].str.lower().str.contains(search_term, na=False)
            | subset["Marke"].str.lower().str.contains(search_term, na=False)
        ]

    # 💶 Preis-Konvertierung
    if "Preis_float" not in subset.columns:
        subset["Preis_float"] = subset["Preis"].apply(money_to_float)

    def unit_price_to_float(s: str) -> float | None:
        if not isinstance(s, str) or not s.strip():
            return None
        s_clean = s.lower().replace("€", "").replace(" ", "")
        m = re.search(r"([\d,.]+)\s*/\s*(kg|g|l|ml)", s_clean)
        if not m:
            return None
        val = float(m.group(1).replace(",", "."))
        unit = m.group(2)
        if unit == "g":
            return val * 1000
        elif unit == "ml":
            return val * 1000
        else:
            return val

    if "Preis_kg_float" not in subset.columns and "Preis_kg" in subset.columns:
        subset["Preis_kg_float"] = subset["Preis_kg"].apply(unit_price_to_float)

    # 🕒 Zeitraum-Filter (Datums-Slider)
    if "Gueltig_von" in subset.columns and "Gueltig_bis" in subset.columns:
        min_date = pd.to_datetime(subset["Gueltig_von"], errors="coerce").min()
        max_date = pd.to_datetime(subset["Gueltig_bis"], errors="coerce").max()

        if pd.notna(min_date) and pd.notna(max_date):
            min_date = min_date.to_pydatetime()
            max_date = max_date.to_pydatetime()

            today = datetime.today()
            limit_min = max(min_date, today - timedelta(days=1))

            selected_range = st.slider(
                "Zeitraum auswählen:",
                min_value=limit_min,
                max_value=max_date,
                value=(limit_min, max_date),
                format="DD.MM.YYYY"
            )

            subset = subset[
                (pd.to_datetime(subset["Gueltig_von"], errors="coerce") <= selected_range[1])
                & (pd.to_datetime(subset["Gueltig_bis"], errors="coerce") >= selected_range[0])
            ]

    # ↕️ Sortieroption
    sort_option = st.selectbox(
        "Sortieren nach:",
        [
            "Kein Sortieren",
            "Preis (aufsteigend)",
            "Preis (absteigend)",
            "Preis pro kg/l (aufsteigend)",
            "Preis pro kg/l (absteigend)",
            "Rabatt (absteigend)"
        ]
    )

    if sort_option == "Preis (aufsteigend)":
        subset = subset.sort_values("Preis_float", ascending=True)
    elif sort_option == "Preis (absteigend)":
        subset = subset.sort_values("Preis_float", ascending=False)
    elif sort_option == "Preis pro kg/l (aufsteigend)" and "Preis_kg_float" in subset.columns:
        subset = subset.sort_values("Preis_kg_float", ascending=True)
    elif sort_option == "Preis pro kg/l (absteigend)" and "Preis_kg_float" in subset.columns:
        subset = subset.sort_values("Preis_kg_float", ascending=False)
    elif sort_option == "Rabatt (absteigend)" and "Rabatt_vs_prev" in subset.columns:
        subset = subset.sort_values("Rabatt_vs_prev", ascending=False)

    # 🔢 Mehr-Anzeigen-Mechanismus
    if "card_limit" not in st.session_state:
        st.session_state.card_limit = 12  # Startwert

    shown_subset = subset.head(st.session_state.card_limit)

    # --- Anzeige ---
    if shown_subset.empty:
        st.info("Keine passenden Produkte gefunden.")
    else:
        cols = st.columns(cols_per_row)

        for i, (_, row) in enumerate(shown_subset.iterrows()):
            with cols[i % cols_per_row]:


                csv_image = row.get("Bildpfad")
                if isinstance(csv_image, str) and csv_image.strip():
                    img_candidate = Path(csv_image)

                    # 🔍 Versuch 1: Vollständiger Pfad im CSV gültig?
                    if img_candidate.exists():
                        st.image(img_candidate.as_posix(), use_container_width=True)

                    # 🔍 Versuch 2: Bild liegt unter data/images/images_edeka
                    elif (CSV_IMG_DIR / img_candidate.name).exists():
                        st.image((CSV_IMG_DIR / img_candidate.name).as_posix(), use_container_width=True)

                    # 🔍 Versuch 3: Fallback in resized
                    elif (IMAGE_DIR / img_candidate.name).exists():
                        st.image((IMAGE_DIR / img_candidate.name).as_posix(), use_container_width=True)

                    # 🔍 Versuch 4: generisches Produktbild
                    else:
                        st.image(get_image_for_product(row["Produkt"]), use_container_width=True)
                else:
                    st.image(get_image_for_product(row["Produkt"]), use_container_width=True)

                # === Produktinfos ===
                full_name = str(row.get("Produkt", ""))
                short_name = short_text(full_name, 60)

                st.markdown(f"**{short_name}**")
                st.caption(f"{row.get('Marke', '')} – {row['Retailer']}")
                st.write(f"💶 **{row['Preis']}** ({row.get('Preis_kg', '')})")

                von = pd.to_datetime(row.get("Gueltig_von"), errors="coerce")
                bis = pd.to_datetime(row.get("Gueltig_bis"), errors="coerce")
                if pd.notna(von) and pd.notna(bis):
                    st.write(f"🗓️ {von:%d.%m.%Y} – {bis:%d.%m.%Y}")

                r = row.get("Rabatt_vs_prev")
                if pd.notna(r) and r > 0:
                    st.markdown(f"<span style='color:green'>💸 Rabatt: {(r * 100):.1f}%</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:gray'>🏷️ Aktion / Kein Rabatt</span>", unsafe_allow_html=True)

                # 🟢 Eindeutiger Key pro Produkt
                widget_key = f"add_btn_{row.name}_{i}"
                state_key = f"add_state_{row.name}_{i}"

                # 🔸 Initialisieren, falls noch nicht vorhanden
                if state_key not in st.session_state:
                    st.session_state[state_key] = False  # False = noch nicht im Warenkorb

                # 🔹 Button-Label abhängig vom Zustand
                button_label = "➖ Entfernen" if st.session_state[state_key] else "➕ Hinzufügen"

                # 🔹 Button anzeigen
                if st.button(button_label, key=widget_key):
                    if st.session_state[state_key]:
                        # Produkt war im Warenkorb → entfernen
                        st.session_state.cart = [
                            item for item in st.session_state.cart
                            if not (
                                    item.get("Produkt") == row["Produkt"]
                                    and item.get("Retailer") == row["Retailer"]
                            )
                        ]
                        st.session_state[state_key] = False  # wieder zu „Hinzufügen“ schalten
                    else:
                        # Produkt war noch nicht im Warenkorb → hinzufügen
                        st.session_state.cart.append(row.to_dict())
                        st.session_state[state_key] = True  # jetzt „Entfernen“ anzeigen

                    # 🔄 Sofortiges Re-Rendern, damit der Button sofort wechselt
                    st.rerun()

        # 🔽 Mehr-Anzeigen-Button
        if len(subset) > st.session_state.card_limit:
            st.markdown("")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔽 Mehr anzeigen"):
                    st.session_state.card_limit += 9
                    st.rerun()
        elif len(subset) > 12:
            st.markdown("")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔼 Weniger anzeigen"):
                    st.session_state.card_limit = 12
                    st.rerun()

    st.divider()

    # --- 🛒 Einkaufswagen-Vorschau ---
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
    favourite_categories = fav_data.get("favourite_categories", [])

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

        date_mask = (
                ((pd.to_datetime(data["Gueltig_von"], errors="coerce") <= today) &
                 (pd.to_datetime(data["Gueltig_bis"], errors="coerce") >= today))
                |
                ((pd.to_datetime(data["Gueltig_von"], errors="coerce") <= tomorrow) &
                 (pd.to_datetime(data["Gueltig_bis"], errors="coerce") >= tomorrow))
        )

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
# Tab 5 – Top Deals (vormals Tab1)
# ---------------------------------------------------
with tab5:
    base = get_base_data("tab1")
    if not base.empty and "Rabatt_vs_prev" in base.columns:
        top_deals = base.sort_values("Rabatt_vs_prev", ascending=False).head(15)
        st.subheader("🔥 Top 15 größte Rabatte heute")

        top_deals_display = top_deals.copy()
        if "Rabatt_vs_prev" in top_deals_display.columns:
            top_deals_display["Rabatt_vs_prev"] = (top_deals_display["Rabatt_vs_prev"] * 100).round(1).astype(str) + "%"

        cols_to_show = [
            c for c in [
                "Retailer", "Produkt", "Marke", "Preis", "Preis_kg", "Vorheriger Preis",
                "Rabatt_vs_prev", "Hinweis", "Nur_online",
                "Gueltig_von", "Gueltig_bis", "UnitPriceLeader"
            ] if c in top_deals_display.columns
        ]

        for col in ["Gueltig_von", "Gueltig_bis"]:
            if col in top_deals_display.columns:
                top_deals_display[col] = pd.to_datetime(
                    top_deals_display[col], errors="coerce"
                ).dt.strftime("%d.%m.%Y")

        st.dataframe(top_deals_display[cols_to_show], use_container_width=True)
