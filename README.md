# ProductShowApp

## 1. Short Project Summary
ProductShowApp is a Streamlit-based product showcase and price-comparison experience for German supermarket offers. It displays offer cards with images, prices, per‑kg pricing, retailers, and validity dates pulled from weekly CSV feeds. The app solves the problem of exploring and comparing large, multi‑retailer catalogs by letting users filter, search, sort, and inspect offers across time windows. Users can rank offers by price, price per unit, or discount, explore price history, and build a lightweight cart and favorites view. The output is an interactive UI that surfaces current offers, historical pricing trends, and personalized recommendation rankings based on an uploaded shopping‑list weighting file.

## 2. Technical Overview
**Data source and format**
- The app ingests multiple retailer CSVs from `/data`, each containing offer metadata such as product name, brand, price, price per kg/l, image path, and validity dates. Retailer identity is inferred from the CSV filename. The app also reads an optional `favourites.json` for preloaded favorites and weights. 【F:app/streamlit_app.py†L16-L18】【F:app/streamlit_app.py†L215-L258】【F:favourites.json†L1-L20】

**Data preprocessing**
- CSVs are concatenated, deduplicated, and enriched with parsed price fields (`Preis_float`, `Preis_kg_float`) and date fields (`Gueltig_von`, `Gueltig_bis`). Discount percentage is computed when previous pricing is available, and additional boolean flags indicate whether an offer overlaps the selected date range or is currently active. 【F:app/streamlit_app.py†L262-L353】

**UI logic (filters, sorting, grouping)**
- The UI is organized into tabs: offer cards, favorites/monitoring, cart, price history, shopping list tokenization, and recommendations. Core filters include retailer multi‑select, search input, and a date‑range slider. Sorting supports price, price per unit, and discount ordering. Pagination ("Mehr anzeigen") limits rendering for performance. 【F:app/streamlit_app.py†L280-L567】【F:app/streamlit_app.py†L571-L1203】

**State handling**
- Streamlit session state stores the cart and per‑row button states for add/remove actions, along with pagination counters for card lists. This keeps interactive state across reruns. 【F:app/streamlit_app.py†L465-L567】【F:app/streamlit_app.py†L1180-L1275】

**Ranking or scoring logic**
- Recommendations are data‑driven: uploaded `personal_weights.json` is used to score each product by token overlap between user weights and a combined “brand + product” text. Results are sorted by score and filtered via optional search terms. 【F:app/streamlit_app.py†L1028-L1212】

**Presentational vs. data‑driven**
- The app is data‑driven. UI elements are directly backed by CSV data (filters, charts, and rankings) and update dynamically based on the selected timeframe and inputs. 【F:app/streamlit_app.py†L262-L353】【F:app/streamlit_app.py†L571-L1212】

## 3. Folder Structure (Core Section)
```
.
├── app/                # Streamlit application logic and UI
├── data/               # Retailer CSV inputs and data scripts
├── images/             # Local product imagery and utilities
├── sammlung/           # Example product collection CSV
├── favourites.json     # Sample favorites/weights source
└── requirements.txt    # Python dependencies
```

**Folder responsibilities**
- **app/** holds the Streamlit UI and all filtering, scoring, and visualization logic.
- **data/** contains the raw retailer CSVs used by the app as primary data inputs.
- **images/** provides local images and scripts for resizing or normalization.
- **sammlung/** contains additional sample data for product collections.
- **favourites.json** provides sample favorites and categories used in the favorites tab.
- **requirements.txt** defines runtime dependencies.

**UI → logic → data flow**
- The UI inputs (search, filters, date range, and toggles) control a filtered view of `data` that is built from the CSVs at startup. The resulting subset feeds card rendering, charts, and recommendation scoring. State (cart contents, pagination) persists via `st.session_state`. 【F:app/streamlit_app.py†L262-L567】【F:app/streamlit_app.py†L1028-L1275】

**Where key responsibilities live**
- **UI components:** `app/streamlit_app.py` (tabs, layout, cards, charts).【F:app/streamlit_app.py†L371-L1275】
- **Data logic:** `app/streamlit_app.py` (CSV loading, parsing, scoring).【F:app/streamlit_app.py†L215-L1212】
- **Configuration:** `requirements.txt` and app‑level constants in `app/streamlit_app.py`.【F:requirements.txt†L1-L6】【F:app/streamlit_app.py†L11-L19】

## 4. Engineering & Design Decisions
- **Framework choice:** Streamlit enables fast iteration on data‑driven UIs and makes it straightforward to connect Pandas transformations to interactive controls and charts, which fits the product‑comparison use case. 【F:app/streamlit_app.py†L1-L12】
- **Scalability & clarity:** The app uses standardized preprocessing (price parsing, date normalization, deduplication) to create reliable filtering and ranking inputs. Pagination keeps rendering responsive when datasets grow. 【F:app/streamlit_app.py†L314-L567】
- **Trade‑offs:** Storing logic in a single Streamlit file keeps onboarding simple but concentrates UI, data loading, and business logic in one module. This favors quick experimentation over modular separation, which would be beneficial if features expand or multiple contributors join. 【F:app/streamlit_app.py†L1-L1275】

## 5. What This Project Demonstrates
- **Product thinking:** It addresses real shopping workflows—filtering by retailer, comparing price per unit, and tracking current vs. historical offers with a cart‑style shortlist. 【F:app/streamlit_app.py†L280-L567】【F:app/streamlit_app.py†L571-L999】
- **UI/data integration:** Inputs directly drive Pandas filtering, charting, and recommendation scoring to create an interactive data exploration tool. 【F:app/streamlit_app.py†L262-L1212】
- **Software structure skills:** Clear organization of app, data, and assets plus consistent parsing utilities show an end‑to‑end data‑to‑UI pipeline. 【F:app/streamlit_app.py†L80-L353】
