"""Application Streamlit pour afficher les animaux - Améliorée"""
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

# Configuration de la page
st.set_page_config(page_title="Animals DB 🦁", layout="wide", initial_sidebar_state="expanded")

# Thème personnalisé
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown("# 🦁 Animals Database - Interactive Explorer")
st.markdown("Explore global biodiversity with detailed data and visualizations")

# Connexion MongoDB
@st.cache_resource
def get_database():
    client = MongoClient(MONGODB_URI)
    return client[DATABASE_NAME]

try:
    db = get_database()
    collection = db[COLLECTION_NAME]
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🔍 Search & Filter")
        
        # Barre de recherche
        search_query = st.text_input("Search animal", placeholder="Ex: Tiger, Lion...")
        
        # Récupérer les valeurs uniques pour les filtres
        habitats = sorted([h for h in collection.distinct("habitat") if h])
        diets = sorted([d for d in collection.distinct("diet") if d])
        statuses = sorted([s for s in collection.distinct("conservation_status") if s])
        
        selected_habitats = st.multiselect("🌍 Habitat", habitats)
        selected_diets = st.multiselect("🍖 Diet", diets)
        selected_statuses = st.multiselect("🛡️ Status", statuses)
    
    # Construire la requête MongoDB
    filter_query = {}
    
    if search_query:
        filter_query["animal_name"] = {"$regex": search_query, "$options": "i"}
    
    if selected_habitats:
        filter_query["habitat"] = {"$in": selected_habitats}
    
    if selected_diets:
        filter_query["diet"] = {"$in": selected_diets}
    
    if selected_statuses:
        filter_query["conservation_status"] = {"$in": selected_statuses}
    
    # Récupérer tous les animaux pour les stats
    all_animals = list(collection.find({}, {"_id": 0}))
    
    # Récupérer les animaux filtrés
    animals = list(collection.find(filter_query, {"_id": 0}).limit(200))
    
    if animals:
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🐾 Total Animals", len(all_animals))
        with col2:
            st.metric("🔎 Results", len(animals))
        with col3:
            habitats_uniq = len(set([a.get('habitat') for a in all_animals if a.get('habitat')]))
            st.metric("🌍 Habitats", habitats_uniq)
        with col4:
            diets_uniq = len(set([a.get('diet') for a in all_animals if a.get('diet')]))
            st.metric("🍖 Diets", diets_uniq)
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Table", "📈 Stats", "📋 Details", "⬇️ Export"])
        
        with tab1:
            st.subheader("Animal List")
            # Créer un dataframe simplifié avec les tags - TRIÉ ALPHABÉTIQUEMENT
            df_simple = []
            sorted_animals = sorted(animals, key=lambda x: x.get('animal_name', '').lower())
            for animal in sorted_animals:
                habitat_display = (animal.get('habitat_tags', [0])[0].capitalize() if animal.get('habitat_tags') else (animal.get('habitat', 'N/A')[:50] + "..." if animal.get('habitat') and len(animal.get('habitat', '')) > 50 else animal.get('habitat', 'N/A')))
                diet_display = (animal.get('diet_tags', [0])[0].capitalize() if animal.get('diet_tags') else (animal.get('diet', 'N/A')[:50] + "..." if animal.get('diet') and len(animal.get('diet', '')) > 50 else animal.get('diet', 'N/A')))
                df_simple.append({
                    'Nom': animal.get('animal_name'),
                    'Scientifique': animal.get('scientific_name', 'N/A'),
                    'Habitat': habitat_display,
                    'Diet': diet_display,
                    'Status': animal.get('conservation_status', 'N/A')
                })
            df_display = pd.DataFrame(df_simple)
            st.dataframe(df_display, use_container_width=True, height=400)
        
        with tab2:
            # Graphiques - Utiliser les tags au lieu des textes complets
            col1, col2 = st.columns(2)
            
            with col1:
                # Extraire les premiers tags diet
                diet_tags_list = []
                for animal in animals:
                    if animal.get('diet_tags'):
                        diet_tags_list.append(animal['diet_tags'][0])
                
                diet_counts = pd.Series(diet_tags_list).value_counts().reset_index()
                diet_counts.columns = ['diet', 'count']
                fig_diet = px.pie(diet_counts, names='diet', values='count', title="📊 Diet Distribution")
                st.plotly_chart(fig_diet, use_container_width=True)
            
            with col2:
                # Extraire les premiers tags habitat
                habitat_tags_list = []
                for animal in animals:
                    if animal.get('habitat_tags'):
                        habitat_tags_list.append(animal['habitat_tags'][0])
                
                habitat_counts = pd.Series(habitat_tags_list).value_counts().reset_index()
                habitat_counts.columns = ['habitat', 'count']
                fig_habitat = px.bar(habitat_counts.head(10), x='habitat', y='count', 
                                    title="🌍 Top 10 Habitats")
                st.plotly_chart(fig_habitat, use_container_width=True)
            
            # Statuts de conservation
            status_list = [a.get('conservation_status') for a in animals if a.get('conservation_status')]
            status_counts = pd.Series(status_list).value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig_status = px.bar(status_counts, x='status', y='count', 
                               title="🛡️ Conservation Status", color='count')
            st.plotly_chart(fig_status, use_container_width=True)
        
        with tab3:
            st.subheader("Animal Details")
            
            selected_animal = st.selectbox(
                "Select an animal:",
                [animal['animal_name'] for animal in sorted(animals, key=lambda x: x.get('animal_name', '').lower())]
            )
            
            animal_detail = next(
                (a for a in animals if a['animal_name'] == selected_animal), 
                None
            )
            
            if animal_detail:
                st.markdown(f"### 🦁 {selected_animal}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Scientific Name:** {animal_detail.get('scientific_name', 'N/A')}")
                with col2:
                    st.write(f"**Habitat:** {animal_detail.get('habitat', 'N/A')}")
                with col3:
                    st.write(f"**Diet:** {animal_detail.get('diet', 'N/A')}")
                
                st.write(f"**Status:** {animal_detail.get('conservation_status', 'N/A')}")
                
                # Description
                description = animal_detail.get('description', 'N/A')
                if description and description != 'N/A':
                    st.markdown(f"**Description:** {description}")
                
                # Key Facts
                key_facts = animal_detail.get('key_facts', [])
                if key_facts and key_facts != [None]:
                    st.markdown("**Key Facts:**")
                    for fact in key_facts:
                        if fact:
                            st.write(f"• {fact}")
                
                # Classification
                classification = animal_detail.get('classification', {})
                if classification:
                    st.markdown("**Classification:**")
                    cols = st.columns(3)
                    for i, (key, val) in enumerate(classification.items()):
                        with cols[i % 3]:
                            st.write(f"*{key}:* {val}")
        
        with tab4:
            st.subheader("Export Data")
            
            # Sélectionner les colonnes
            df_export = pd.DataFrame(animals)
            columns_to_export = st.multiselect(
                "Columns to export",
                df_export.columns.tolist(),
                default=['animal_name', 'scientific_name', 'habitat', 'diet', 'conservation_status']
            )
            
            if columns_to_export:
                df_export_filtered = df_export[columns_to_export]
                
                # CSV
                csv = df_export_filtered.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="animals_export.csv",
                    mime="text/csv"
                )
    else:
        st.info("❌ No animals found. Try adjusting your filters.")
        
except Exception as e:
    st.error(f"❌ MongoDB Connection Error: {e}")
    st.info("Make sure MongoDB is running on mongodb://localhost:27017")
