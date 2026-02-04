"""Application Streamlit pour afficher les animaux - Améliorée"""
from utils import extract_diet_category, extract_habitat_category, extract_countries, extract_countries_from_text
from search_client import SearchClient
from streamlit_folium import st_folium
import folium
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

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
        data = list(collection.find({}, {"_id": 0}))

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
                'animal_name': item.get('animal_name', 'Unknown'),
                'scientific_name': item.get('scientific_name') or 'N/A',
                'conservation_status': clean_status,
                'diet': item.get('diet') or 'Unknown',
                'habitat': item.get('habitat') or 'Unknown',
                'description': item.get('description') or 'No description available.',
                'key_facts': item.get('key_facts', []),
                'locations': item.get('locations', []),  # Handle missing locations
                'image_url': item.get('image_url'),
                'source_url': item.get('url'),
                'facts': item.get('facts', {})  # Add facts dict for extraction
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
        st.header("Filters")
        diet_choices = sorted([c for c in df_animals["Diet Category"].dropna().unique() if c and c != 'Unknown'])
        habitat_choices = sorted([c for c in df_animals["Habitat Category"].dropna().unique() if c and c != 'Unknown'])

        selected_diets = st.multiselect("Diet", options=diet_choices, default=[])
        selected_habitats = st.multiselect("Habitat", options=habitat_choices, default=[])

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

    animals_count = len(filtered_df)

    # ---------------------------------------------------------
    # NAVIGATION STATE MANAGEMENT
    # ---------------------------------------------------------
    if 'selected_animal' not in st.session_state:
        st.session_state.selected_animal = None

    def show_detail(animal_name):
        st.session_state.selected_animal = animal_name

    def back_to_home():
        st.session_state.selected_animal = None

    # ---------------------------------------------------------
    # VIEW: HOME (LIST + MAP)
    # ---------------------------------------------------------
    if st.session_state.selected_animal is None:
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

        # Select columns to display
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
                    show_detail(row['animal_name'])
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
    # VIEW: DETAIL
    # ---------------------------------------------------------
    else:
        # Fetch detailed data
        animal_name = st.session_state.selected_animal
        animal_data = df_animals[df_animals['animal_name'] == animal_name]

        if not animal_data.empty:
            animal = animal_data.iloc[0]

            # Helper for badges
            def get_diet_badge(diet):
                d = diet.lower() if diet else ""
                if 'carnivore' in d:
                    return "badge-carnivore"
                if 'herbivore' in d:
                    return "badge-herbivore"
                if 'omnivore' in d:
                    return "badge-omnivore"
                return "badge-default"

            def get_habitat_badge(habitat):
                h = habitat.lower() if habitat else ""
                if 'forest' in h:
                    return "badge-forest"
                if 'ocean' in h:
                    return "badge-ocean"
                if 'desert' in h:
                    return "badge-desert"
                return "badge-default"

            # Navigation
            if st.button("Back to List"):
                back_to_home()
                st.rerun()

            # Hero Section
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 32px; border-radius: 8px; margin-bottom: 24px; color: white;">
                <h1 class="hero-title">{animal['animal_name']}</h1>
                <p style="font-style: italic; opacity: 0.8; font-size: 1rem; margin-bottom: 16px;">{animal.get('scientific_name', 'Unknown Scientific Name')}</p>
                <div>
                    <span class="badge {get_diet_badge(animal.get('Diet Category', ''))}">{animal.get('Diet Category', 'Unknown Diet')}</span>
                    <span class="badge {get_habitat_badge(animal.get('Habitat Category', ''))}">{animal.get('Habitat Category', 'Unknown Habitat')}</span>
                    <span class="badge badge-default">Status: {animal.get('conservation_status', 'Unknown')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Only show description if it exists
            if animal.get('description'):
                st.markdown("### Description")
                st.write(animal.get('description'))
                st.divider()

            st.markdown("### Habitat")
            # Try to get habitat from facts first, then fallback to habitat field
            habitat_info = 'Unknown'
            if isinstance(animal.get('facts'), dict) and animal['facts'].get('Habitat'):
                habitat_info = animal['facts']['Habitat']
            elif animal.get('habitat'):
                habitat_info = animal['habitat']
            st.write(habitat_info)

            st.divider()

            c1, c2 = st.columns(2)

            with c1:
                st.markdown("### Key Facts")
                facts = animal.get('key_facts', [])
                if isinstance(facts, list):
                    for fact in facts:
                        if fact:
                            st.write(f"• {fact}")

            with c2:
                st.markdown("### More Info")
                if animal.get('image_url'):
                    try:
                        st.image(animal.get('image_url'), use_container_width=True)
                    except Exception:
                        pass
                if animal.get('source_url'):
                    if hasattr(st, "link_button"):
                        st.link_button("View Source", animal.get('source_url'))
                    else:
                        st.markdown(f"[View Source]({animal.get('source_url')})")

        else:
            st.error("Animal not found.")
            if st.button("Back to Home"):
                back_to_home()
                st.rerun()

    if filtered_df.empty and st.session_state.selected_animal is None:
        st.info("No animals found. Adjust search.")

except Exception as e:
    st.error(f"Connection Error: {e}")
