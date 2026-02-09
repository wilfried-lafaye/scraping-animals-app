"""Application Streamlit pour afficher les animaux - Améliorée"""
from utils import extract_diet_category, extract_habitat_category, extract_countries, extract_countries_from_text
from search_client import SearchClient
from streamlit_folium import st_folium
import folium
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import requests
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME


@st.cache_data(ttl=3600)
def get_wikipedia_image(animal_name: str, scientific_name: str = None) -> str | None:
    """Fetch image URL from Wikipedia API with caching."""
    base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"

    for name in [animal_name, scientific_name]:
        if not name:
            continue

        wiki_name = name.strip().replace(" ", "_")

        try:
            response = requests.get(
                f"{base_url}{wiki_name}",
                headers={"User-Agent": "AnimalScraper/1.0"},
                timeout=5
            )

            if response.ok:
                data = response.json()
                if 'originalimage' in data:
                    return data['originalimage'].get('source')
                elif 'thumbnail' in data:
                    return data['thumbnail'].get('source')
        except Exception:
            continue

    return None


@st.cache_data(ttl=3600)
def get_wikipedia_description(animal_name: str, scientific_name: str = None) -> str | None:
    """Fetch description from Wikipedia API with caching."""
    base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"

    for name in [scientific_name, animal_name]:
        if not name:
            continue

        wiki_name = name.strip().replace(" ", "_")

        try:
            response = requests.get(
                f"{base_url}{wiki_name}",
                headers={"User-Agent": "AnimalScraper/1.0"},
                timeout=5
            )

            if response.ok:
                data = response.json()
                extract = data.get('extract')
                # Filter out meta descriptions (avoid sentences about "this article" or "this page")
                if extract and len(extract) > 50:
                    # Remove sentences that start with "Enjoy", "This article", "This is an article"
                    sentences = extract.split('. ')
                    clean_sentences = []
                    for sentence in sentences:
                        if not any(phrase in sentence for phrase in [
                            'Enjoy this',
                            'This article',
                            'This is an article',
                            'expertly researched',
                            'high quality pictures'
                        ]):
                            clean_sentences.append(sentence)

                    clean_extract = '. '.join(clean_sentences).strip()
                    if clean_extract and len(clean_extract) > 50:
                        return clean_extract
        except Exception:
            continue

    return None


# Configuration de la page
st.set_page_config(
    page_title="Animals DB",
    layout="wide",
    initial_sidebar_state="expanded")

# Thème personnalisé
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Inter:wght@400;500&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #0f172a;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.5rem;
        margin-top: 0 !important;
    }

    /* Hero Title */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
    }

    /* Custom Badge */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 6px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .badge-carnivore { background-color: #fee2e2; color: #991b1b; }
    .badge-herbivore { background-color: #dcfce7; color: #166534; }
    .badge-omnivore { background-color: #fef9c3; color: #854d0e; }
    .badge-forest { background-color: #ecfccb; color: #3f6212; }
    .badge-ocean { background-color: #dbeafe; color: #1e40af; }
    .badge-desert { background-color: #ffedd5; color: #9a3412; }
    .badge-default { background-color: #f1f5f9; color: #475569; }

    /* Card Style */
    .info-card {
        background-color: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        margin-bottom: 16px;
        border: 1px solid #e2e8f0;
    }

    .metric-card {
        background-color: white;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .metric-card h3 {
        font-size: 1.5rem;
        margin: 0;
    }
    .metric-card p {
        font-size: 0.85rem;
        color: #64748b;
        margin: 0;
        text-transform: uppercase;
        font-weight: 500;
    }

    /* Chip/Pill Filter Buttons */
    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
    }
    .chip {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
        color: #64748b;
    }
    .chip:hover {
        border-color: #cbd5e1;
        background-color: #f1f5f9;
    }
    .chip.active {
        background-color: #0f172a;
        color: white;
        border-color: #0f172a;
    }
    .chip-icon {
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown("# 🐾 World Animals")
st.markdown("Explore global biodiversity and discover the animals of our planet.")


# Connexion MongoDB

@st.cache_resource
def get_database():
    import time
    for attempt in range(5):
        try:
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            return client[DATABASE_NAME]
        except Exception:
            if attempt == 4:
                raise
            time.sleep(1.5)


try:
    db = get_database()
    collection = db[COLLECTION_NAME]

    # ---------------------------------------------------------
    # DATA LOADING & PROCESSING
    # ---------------------------------------------------------
    # Load data from MongoDB (Cached)
    @st.cache_data(ttl=30)
    def load_data():
        data = list(collection.find({}))

        # Flatten data for DataFrame
        processed_data = []
        for item in data:
            # Clean conservation status - take only the first one if multiple, remove invalid ones
            raw_status = item.get('conservation_status') or 'Unknown'
            valid_statuses = [
                'Least Concern', 'Near Threatened', 'Vulnerable', 'Endangered',
                'Critically Endangered', 'Extinct in the Wild', 'Extinct',
                'Data Deficient', 'Not Evaluated', 'Not Listed'
            ]
            # Check if status contains comma (multiple statuses)
            if ',' in str(raw_status):
                # Take the first valid status
                parts = [p.strip() for p in str(raw_status).split(',')]
                clean_status = 'Unknown'
                for part in parts:
                    if part in valid_statuses:
                        clean_status = part
                        break
            elif raw_status in valid_statuses:
                clean_status = raw_status
            else:
                clean_status = 'Unknown'

            # Extract key fields directy from flat structure
            row = {
                'id': str(item.get('_id')),
                'animal_name': item.get('animal_name', 'Unknown'),
                'scientific_name': item.get('scientific_name') or 'N/A',
                'conservation_status': clean_status,
                'diet': item.get('diet') or 'Unknown',
                'habitat': item.get('habitat') or 'Unknown',
                'description': item.get('description') or 'No description available.',
                'key_facts': item.get('key_facts', []),
                'locations': item.get('locations', []),  # Handle missing locations
                'image_url': item.get('image_url'),
                'url': item.get('url'),  # Fix: Ensure 'url' key exists for UI logic
                'source_url': item.get('url'),
                'facts': item.get('facts', {}),  # Add facts dict for extraction
                'classification': item.get('classification', {}),  # Add classification object
                # New standardized fields
                'top_speed_kph': item.get('top_speed_kph', 0),
                'weight_min_kg': item.get('weight_min_kg', 0),
                'lifespan_min_years': item.get('lifespan_min_years', 0),
                # data sources
                'description_source': item.get('description_source'),
                'image_source': item.get('image_source'),
                'stats_source': item.get('stats_source'),
                'weight_source': item.get('weight_source'),
                'length_source': item.get('length_source'),
                'lifespan_source': item.get('lifespan_source')
            }

            # Extraction logic
            # Use facts['Diet'] if available, fallback to diet field
            diet_text = row.get('diet')
            if isinstance(row.get('facts'), dict) and 'Diet' in row['facts']:
                diet_text = row['facts']['Diet']
            row['Diet Category'] = extract_diet_category(diet_text)

            # Priority order for habitat: facts['Habitat'] > habitat field > locations
            habitat_text = None
            if isinstance(row.get('facts'), dict) and 'Habitat' in row['facts']:
                habitat_text = row['facts']['Habitat']
            elif row.get('habitat'):
                habitat_text = row.get('habitat')
            elif isinstance(row.get('locations'), list) and len(row['locations']) > 0:
                # Join locations to create habitat text
                habitat_text = ', '.join(row['locations'])
            row['Habitat Category'] = extract_habitat_category(habitat_text)

            # Country extraction: Try locations first, then fallback to habitat text
            countries = extract_countries(row['locations'])
            if not countries and row['habitat'] != 'Unknown':
                countries = extract_countries_from_text(row['habitat'])

            row['Countries'] = countries

            processed_data.append(row)

        df = pd.DataFrame(processed_data)
        return df

    df_animals = load_data()
    search_client = SearchClient()

    # ---------------------------------------------------------
    # MAIN LAYOUT & SEARCH
    # ---------------------------------------------------------
    # Simple Search Bar
    search_col1, search_col2 = st.columns([1, 2])
    with search_col2:
        search_query = st.text_input(
            "Search",
            placeholder="Search animal (e.g. Panthera, Eagle)...",
            label_visibility="collapsed")

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")

        # --- Diet Dropdown ---
        diet_choices = sorted([c for c in df_animals["Diet Category"].dropna().unique() if c])
        diet_icons = {'Carnivore': '🥩', 'Herbivore': '🌿', 'Omnivore': '🍽️', 'Insectivore': '🦗', 'Piscivore': '🐟'}
        diet_options = [f"{diet_icons.get(diet, '🍴')} {diet}" for diet in diet_choices]
        diet_labels = {opt: diet for opt, diet in zip(diet_options, diet_choices)}

        st.markdown("**🍽️ Diet**")
        selected_diet_display = st.multiselect(
            "Diet",
            options=diet_options,
            default=[],
            label_visibility="collapsed"
        )
        selected_diets = [diet_labels[opt] for opt in selected_diet_display]

        # --- Habitat Dropdown ---
        habitat_choices = sorted([c for c in df_animals["Habitat Category"].dropna().unique() if c])
        habitat_icons = {'Forest': '🌲', 'Ocean': '🌊', 'Desert': '🏜️', 'Grassland': '🌾', 'Wetland': '🌿', 'Mountain': '🏔️', 'Tundra': '❄️', 'Urban': '🏙️'}
        habitat_options = [f"{habitat_icons.get(habitat, '🌍')} {habitat}" for habitat in habitat_choices]
        habitat_labels = {opt: habitat for opt, habitat in zip(habitat_options, habitat_choices)}

        st.markdown("**🏠 Habitat**")
        selected_habitat_display = st.multiselect(
            "Habitat",
            options=habitat_options,
            default=[],
            label_visibility="collapsed"
        )
        selected_habitats = [habitat_labels[opt] for opt in selected_habitat_display]

        st.divider()
        st.subheader("Advanced Filters")

        # Helper to safely get min/max for sliders
        def safe_min_max(column):
            if df_animals.empty:
                return 0.0, 100.0
            val_min = float(df_animals[column].min())
            val_max = float(df_animals[column].max())
            if val_min == val_max:
                val_max += 1
            return val_min, val_max

        # Weight Slider
        w_min, w_max = safe_min_max('weight_min_kg')
        weight_range = st.slider("Min Weight (kg)",
                                 min_value=0.0, max_value=w_max,
                                 value=(0.0, w_max), step=0.1)

        # Speed Slider
        s_min, s_max = safe_min_max('top_speed_kph')
        speed_range = st.slider("Top Speed (km/h)",
                                min_value=0.0, max_value=s_max,
                                value=(0.0, s_max), step=1.0)

        # Sort options
        st.divider()
        sort_option = st.selectbox("Sort By", options=["Name (A-Z)", "Speed (Fastest)", "Weight (Heaviest)", "Lifespan (Longest)"])

    # ---------------------------------------------------------
    # FILTERING LOGIC (SEARCH + FILTERS)
    # ---------------------------------------------------------
    filtered_df = df_animals.copy()

    if search_query:
        if search_client.is_connected():
            es_results = search_client.search_animals(search_query)
            # Filter and preserve order (roughly, or just filter)
            # Using isin allows filtering, but we might want to prioritize ES matches
            if es_results:
                filtered_df = filtered_df[filtered_df['animal_name'].isin(es_results)]
            else:
                filtered_df = filtered_df.iloc[0:0]
        else:
            # Fallback to string matching
            filtered_df = filtered_df[filtered_df['animal_name'].str.contains(
                search_query, case=False, na=False)]
    # Apply sidebar filters
    if len(filtered_df):
        if selected_diets:
            filtered_df = filtered_df[filtered_df["Diet Category"].isin(selected_diets)]
        if selected_habitats:
            filtered_df = filtered_df[filtered_df["Habitat Category"].isin(selected_habitats)]

        # Apply Advanced Filters
        filtered_df = filtered_df[
            (filtered_df['weight_min_kg'] >= weight_range[0])
            & (filtered_df['weight_min_kg'] <= weight_range[1])
        ]
        filtered_df = filtered_df[
            (filtered_df['top_speed_kph'] >= speed_range[0])
            & (filtered_df['top_speed_kph'] <= speed_range[1])
        ]

    animals_count = len(filtered_df)

    # ---------------------------------------------------------
    # NAVIGATION STATE MANAGEMENT
    # ---------------------------------------------------------
    if 'selected_animal_id' not in st.session_state:
        st.session_state.selected_animal_id = None

    def show_detail(animal_id):
        st.session_state.selected_animal_id = animal_id

    def back_to_home():
        st.session_state.selected_animal_id = None

    # ---------------------------------------------------------
    # VIEW: HOME (LIST + MAP)
    # ---------------------------------------------------------
    if st.session_state.selected_animal_id is None:
        # Métriques cards
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(
            f'<div class="metric-card"><h3>{len(df_animals)}</h3><p>Total Animals</p></div>',
            unsafe_allow_html=True)
        c2.markdown(
            f'<div class="metric-card"><h3>{animals_count}</h3><p>Results</p></div>',
            unsafe_allow_html=True)
        c3.markdown(
            f'<div class="metric-card"><h3>{len([h for h in filtered_df["Habitat Category"].unique() if h and h != "Unknown"])}</h3><p>Habitats</p></div>',
            unsafe_allow_html=True)
        c4.markdown(
            f'<div class="metric-card"><h3>{len([d for d in filtered_df["Diet Category"].unique() if d and d != "Unknown"])}</h3><p>Diets</p></div>',
            unsafe_allow_html=True)

        st.markdown("### Animal List")

        # Pagination controls
        if 'page' not in st.session_state:
            st.session_state.page = 1
        items_per_page = st.selectbox("Items per page", [10, 20, 50], index=1)
        total_pages = max(1, (len(filtered_df) + items_per_page - 1) // items_per_page)
        if st.session_state.page > total_pages:
            st.session_state.page = total_pages

        prev_col, page_col, next_col = st.columns([1, 2, 1])
        with prev_col:
            if st.button("← Prev", disabled=st.session_state.page <= 1):
                st.session_state.page -= 1
                st.rerun()
        with page_col:
            st.markdown(f"Page {st.session_state.page} / {total_pages}")
        with next_col:
            if st.button("Next →", disabled=st.session_state.page >= total_pages):
                st.session_state.page += 1
                st.rerun()

        # Sorting Logic
        if "Speed" in sort_option:
            df_sorted = filtered_df.sort_values('top_speed_kph', ascending=False)
        elif "Weight" in sort_option:
            df_sorted = filtered_df.sort_values('weight_min_kg', ascending=False)
        elif "Lifespan" in sort_option:
            df_sorted = filtered_df.sort_values('lifespan_min_years', ascending=False)
        else:
            df_sorted = filtered_df.sort_values('animal_name')
        start_idx = (st.session_state.page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        df_display = df_sorted.iloc[start_idx:end_idx]

        # Grid Layout for Animal Names (Buttons)
        cols = st.columns(5)
        for idx, (index, row) in enumerate(df_display.iterrows()):
            # Use modulo to cycle through columns
            col = cols[idx % 5]
            with col:
                if st.button(row['animal_name'], key=f"btn_{index}_{idx}", use_container_width=True):
                    show_detail(row['id'])
                    st.rerun()

        st.divider()

        # Map Section
        st.markdown("### Global Distribution")

        # Prepare map data
        country_counts = {}
        for countries in filtered_df['Countries']:
            for country in countries:
                country_counts[country] = country_counts.get(country, 0) + 1

        df_map = pd.DataFrame(list(country_counts.items()), columns=['iso_a3', 'count'])

        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

        if not df_map.empty:
            choropleth = folium.Choropleth(
                geo_data="https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json",
                name="choropleth",
                data=df_map,
                columns=["iso_a3", "count"],
                key_on="feature.id",
                fill_color="YlGnBu",
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name="Number of Animals",
                highlight=True)
            choropleth.geojson.add_child(folium.features.GeoJsonTooltip(fields=['name'], labels=False, style=(
                "background-color: white; color: #333333; font-family: 'Inter'; font-size: 12px; padding: 10px;")))
            choropleth.add_to(m)

        st_folium(m, width=1200, height=500, use_container_width=True)

        st.divider()

        # Charts section
        st.markdown("### Insights")
        if not filtered_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                diet_counts = filtered_df["Diet Category"].value_counts().reset_index()
                diet_counts.columns = ["Diet", "Count"]
                fig1 = px.bar(diet_counts, x="Diet", y="Count", title="Diet Distribution", text="Count")
                fig1.update_traces(textposition='outside')
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                conservation_counts = filtered_df[filtered_df["conservation_status"] != "Unknown"]["conservation_status"].value_counts().reset_index()
                conservation_counts.columns = ["Status", "Count"]
                fig2 = px.pie(conservation_counts, values="Count", names="Status", title="Conservation Status Distribution")
                st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------------
    # VIEW: DETAIL (Timeline/Story Style)
    # ---------------------------------------------------------
    else:
        # Fetch detailed data
        animal_id = st.session_state.selected_animal_id
        animal_data = df_animals[df_animals['id'] == animal_id]

        if not animal_data.empty:
            animal = animal_data.iloc[0]

            # Back button
            if st.button("← Back to Animals", type="secondary"):
                back_to_home()
                st.rerun()

            # =============================================
            # HERO HEADER (Always visible)
            # =============================================
            hero_col1, hero_col2 = st.columns([1, 3])

            with hero_col1:
                # Try existing image, then Wikipedia fallback
                image_url = animal.get('image_url')

                if not image_url or not image_url.startswith('http'):
                    # Try Wikipedia fallback
                    image_url = get_wikipedia_image(
                        animal['animal_name'],
                        animal.get('scientific_name')
                    )

                if image_url:
                    try:
                        st.image(image_url, use_container_width=True)
                    except Exception:
                        st.info("🦁 Image unavailable")
                else:
                    st.info("🦁 No image")

            with hero_col2:
                st.title(animal['animal_name'])
                st.caption(f"*{animal.get('scientific_name') or 'Scientific name unknown'}*")

                # Status badges in a row
                badge_cols = st.columns(4)

                # Diet badge with correct icon
                with badge_cols[0]:
                    diet_cat = animal.get('Diet Category', 'Unknown')
                    diet_icons = {'Carnivore': '🥩', 'Herbivore': '🌿', 'Omnivore': '🍽️', 'Insectivore': '🦗', 'Piscivore': '🐟'}
                    diet_icon = diet_icons.get(diet_cat, '🍴')
                    st.success(f"{diet_icon} {diet_cat}")

                with badge_cols[1]:
                    st.info(f"🌍 {animal.get('Habitat Category', 'Unknown')}")
                with badge_cols[2]:
                    status = animal.get('conservation_status', 'Unknown')
                    if 'endangered' in status.lower():
                        st.error(f"⚠️ {status}")
                    elif 'vulnerable' in status.lower() or 'near threatened' in status.lower():
                        st.warning(f"⚠️ {status}")
                    else:
                        st.info(f"ℹ️ {status}")

            # =============================================
            # QUICK STATS (Always visible under hero)
            # =============================================
            with st.container(border=True):
                stat_cols = st.columns(4)

                with stat_cols[0]:
                    speed = animal.get('top_speed_kph', 0)
                    st.metric("⚡ Top Speed", f"{speed} km/h" if speed else "N/A")

                with stat_cols[1]:
                    weight = animal.get('weight_min_kg', 0)
                    label = "⚖️ Weight"
                    if animal.get('weight_source') == 'wikidata':
                        label += " (✨)"
                    st.metric(label, f"{weight} kg" if weight else "N/A")

                with stat_cols[2]:
                    lifespan = animal.get('lifespan_min_years', 0)
                    label = "🕐 Lifespan"
                    if animal.get('lifespan_source') == 'wikidata':
                        label += " (✨)"
                    st.metric(label, f"{lifespan} yrs" if lifespan else "N/A")

                with stat_cols[3]:
                    litter = None
                    if isinstance(animal.get('facts'), dict):
                        litter = animal['facts'].get('Litter Size') or animal['facts'].get('Average Litter Size')
                    st.metric("🐣 Litter", litter if litter else "N/A")

            # =============================================
            # TABS NAVIGATION
            # =============================================
            tab1, tab2, tab3 = st.tabs(["📋 Overview", "📊 All Facts", "🧬 Classification"])

            # ------------------------------------------
            # TAB 1: OVERVIEW (2-column layout)
            # ------------------------------------------
            with tab1:
                # Row 1: Fun Fact + Habitat side by side
                overview_col1, overview_col2 = st.columns(2)

                with overview_col1:
                    # Fun Fact Card
                    fun_fact = None
                    if isinstance(animal.get('facts'), dict):
                        fun_fact = animal['facts'].get('Fun Fact')

                    with st.container(border=True):
                        st.markdown("**💡 Fun Fact**")
                        if fun_fact:
                            st.write(fun_fact)
                        else:
                            st.caption("No fun fact available.")

                with overview_col2:
                    # Habitat Card
                    with st.container(border=True):
                        st.markdown("**🌍 Habitat**")

                        habitat_info = 'Unknown'
                        if isinstance(animal.get('facts'), dict) and animal['facts'].get('Habitat'):
                            habitat_info = animal['facts']['Habitat']
                        elif animal.get('habitat'):
                            habitat_info = animal['habitat']

                        st.write(habitat_info)

                # Row 2: Location + Conservation
                loc_col1, loc_col2 = st.columns(2)

                with loc_col1:
                    with st.container(border=True):
                        st.markdown("**📍 Found In**")
                        locations = animal.get('locations', [])
                        if isinstance(locations, list) and locations:
                            st.write(", ".join(set(locations)))
                        else:
                            st.caption("Unknown")

                with loc_col2:
                    with st.container(border=True):
                        st.markdown("**🛡️ Conservation**")
                        st.write(animal.get('conservation_status', 'Unknown'))

                # Row 3: Description (full width) - with Wikipedia fallback
                description = animal.get('description')

                # Clean up meta descriptions from scraped data
                if description:
                    bad_phrases = [
                        'Enjoy this expertly researched article',
                        'including where',
                        'what they eat & much more',
                        'Now with high quality pictures'
                    ]
                    # If description contains these phrases, skip it
                    if any(phrase in str(description) for phrase in bad_phrases):
                        description = None

                # Try Wikipedia if no description or too short
                if not description or len(str(description)) < 50:
                    description = get_wikipedia_description(
                        animal['animal_name'],
                        animal.get('scientific_name')
                    )

                if description:
                    with st.container(border=True):
                        desc_header = "**📖 Description**"
                        if animal.get('description_source') == 'wikipedia':
                            desc_header += " *(✨ Wikipedia)*"
                        st.markdown(desc_header)
                        st.write(description)

            # ------------------------------------------
            # TAB 2: ALL FACTS
            # ------------------------------------------
            with tab2:
                with st.container(border=True):
                    st.markdown("**📋 Complete Profile**")

                    all_facts = {}
                    if isinstance(animal.get('facts'), dict):
                        all_facts.update(animal['facts'])
                    if isinstance(animal.get('physical_characteristics'), dict):
                        all_facts.update(animal['physical_characteristics'])

                    excluded_keys = {
                        'Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Scientific Name',
                        'Fun Fact', 'Description', 'Diet', 'Diet Category', 'Habitat',
                        'Top Speed', 'Weight', 'Lifespan', 'Litter Size', 'Average Litter Size'
                    }

                    valid_facts = {}
                    for k, v in all_facts.items():
                        if k in excluded_keys or k.title() in excluded_keys:
                            continue
                        if v is None:
                            continue
                        v_str = str(v).strip()
                        if not v_str or v_str.lower() in ['n/a', 'none', 'unknown', 'null']:
                            continue
                        valid_facts[k] = v_str

                    if valid_facts:
                        fact_keys = sorted(valid_facts.keys())
                        for i in range(0, len(fact_keys), 3):
                            cols = st.columns(3)
                            for j, col in enumerate(cols):
                                if i + j < len(fact_keys):
                                    key = fact_keys[i + j]
                                    with col:
                                        st.caption(key.upper())
                                        st.write(valid_facts[key])
                    else:
                        st.caption("No additional facts available.")

            # ------------------------------------------
            # TAB 3: CLASSIFICATION
            # ------------------------------------------
            with tab3:
                classification = animal.get('classification', {})

                if classification:
                    with st.container(border=True):
                        st.markdown("**🧬 Taxonomy**")

                        tax_levels = ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus']
                        tax_cols = st.columns(len(tax_levels))

                        for i, level in enumerate(tax_levels):
                            val = classification.get(level, 'N/A')
                            with tax_cols[i]:
                                st.caption(level.upper())
                                st.write(val if val else "N/A")
                else:
                    st.info("No classification data available.")

                # Source Card - A-Z Animals Link & Others
                with st.container(border=True):
                    st.markdown("**📄 Data Sources**")

                    # Original Source
                    az_url = animal.get('url')
                    if az_url:
                        st.write(f"🔗 [A-Z Animals]({az_url}) (Base Data)")

                    # Enrichment Sources
                    sources = []
                    if animal.get('description_source') == 'wikipedia':
                        sources.append("📖 Description: Wikipedia")
                    if animal.get('image_source') == 'wikipedia':
                        sources.append("🖼️ Image: Wikipedia")
                    if animal.get('stats_source') == 'wikidata':
                        sources.append("⚖️ Stats: Wikidata")

                    if sources:
                        for s in sources:
                            st.caption(f"✨ {s}")
                    else:
                        st.caption("No external enrichment sources used.")

        else:
            st.error("Animal not found.")
            if st.button("Back to Home"):
                back_to_home()
                st.rerun()

    if filtered_df.empty and st.session_state.selected_animal_id is None:
        st.info("No animals found. Adjust search.")

except Exception as e:
    st.error(f"Connection Error: {e}")
