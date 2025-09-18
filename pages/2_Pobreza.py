import pandas as pd
import unicodedata
import geopandas as gpd
import folium
from folium.features import GeoJson, GeoJsonTooltip
from streamlit_folium import st_folium
import streamlit as st

if 'page' not in st.session_state:
    st.session_state.page = 'mapa_pobreza_dep'

if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None

def change_page():
    st.session_state.page = 'mapa_dep_censal'
def volver():
    st.session_state.page = 'mapa_pobreza_dep'

if st.session_state.page == 'mapa_pobreza_dep':
    df = pd.read_csv("csv/DEPARTAMENTOS SHEET_data.csv", sep=';', encoding='utf-8', low_memory=False)
    df_pobreza = df[['Departamento','Nivel de incidencia de pobreza crónica', 'Provincia', 'Población']].copy()

    gdf = gpd.read_file("departamentos/pxdptodatosok.shp")

    st.set_page_config(page_title="Datos pobreza Argentina 2025", layout='wide')

    st.markdown(
        """
        <style>
        .st-emotion-cache-5qfegl{
            background-color: #3B48FF;
            color: white;
        }
        .st-emotion-cache-5qfegl:hover{
            background-color: #16008C;
        }
        </style>
        """,unsafe_allow_html=True
    )

    def normalizar_textos(s):
        if pd.isna(s):
            return ""
        s = s.lower()
        s = "".join(
            c for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )
        # Quitar espacios dobles
        s = " ".join(s.split())
        return s


    gdf["departamen_norm"] = gdf["departamen"].apply(normalizar_textos)
    gdf['provincia_norm'] = gdf['provincia'].apply(normalizar_textos)

    df_pobreza['departamento_nombre'] = df_pobreza['Departamento'].apply(normalizar_textos)
    df_pobreza['provincia_nombre'] = df_pobreza['Provincia'].apply(normalizar_textos)


    correcciones_dep = {
        "o'higgins": "o higgins",
        "o' higgins": "o higgins",
        'juan bautista alberdi': 'juan b. alberdi',
        'general juan facundo quiroga': 'general juan f. quiroga',
        'comuna 01': 'comuna 1',
        'comuna 02': 'comuna 2',
        'comuna 03': 'comuna 3',
        'comuna 04': 'comuna 4',
        'comuna 05': 'comuna 5',
        'comuna 06': 'comuna 6',
        'comuna 07': 'comuna 7',
        'comuna 08': 'comuna 8',
        'comuna 09': 'comuna 9'
    }
    correcciones_bsas = {
        'partidos del agba': 'buenos aires',
        'ciudad de buenos aires': 'ciudad autonoma de buenos aires',
        'buenos aires (sin agba)': 'buenos aires',
        'provincia de buenos aires': 'buenos aires'
    }

    # Aplicar correcciones departamentos
    df_pobreza['departamento_nombre'] = df_pobreza['departamento_nombre'].replace(correcciones_dep)
    gdf['departamen_norm'] = gdf['departamen_norm'].replace(correcciones_dep)
    # Aplicar correcciones provincias
    df_pobreza['provincia_nombre'] = df_pobreza['provincia_nombre'].replace(correcciones_bsas)
    gdf['provincia_norm'] = gdf['provincia_norm'].replace(correcciones_bsas)



    gdf = gdf.merge(
        df_pobreza, 
        left_on=['departamen_norm' ,'provincia_norm'], 
        right_on=['departamento_nombre', 'provincia_nombre'], 
        how='inner')


    #Creamos un map para trabajar mejor con los datos de pobreza
    mapeo_pobreza = {
        'Muy bajo (0 - 0,99%)': 0.5,
        'Bajo (1 - 4,99%)': 3.0,
        'Moderado (5 - 9,99%)': 7.5,
        'Alto (10 - 14,99%)': 12.5,
        'Muy alto (15 - 24,99%)': 20.0,
        'Crítico (25 - 100%)': 37.5
    }
    gdf['nivel_pobreza'] = gdf['Nivel de incidencia de pobreza crónica'].map(mapeo_pobreza)
    df_pobreza['nivel_pobreza'] = df_pobreza['Nivel de incidencia de pobreza crónica'].map(mapeo_pobreza)

    #Creamos el mapa
    mapa = folium.Map(location=[-38.0, -63.0], zoom_start=5)


    #Muy bajo, Bajo, Moderado, Alto, Muy alto, Crítico
    colores = ['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027']

    def style_function(pobreza):
        cant_pobreza = pobreza['properties'].get('nivel_pobreza')
        if cant_pobreza is None:
            return {'fillColor': '#808080', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
        if 0 <= cant_pobreza <= 1:
            idx = 0
        elif 1 < cant_pobreza <= 5:
            idx = 1
        elif 5 < cant_pobreza <= 10:
            idx = 2
        elif 10 < cant_pobreza <= 15:
            idx = 3
        elif 15 < cant_pobreza <= 25:
            idx = 4
        elif 25 < cant_pobreza <= 100:
            idx = 5
        
        return {
            'fillColor': colores[idx],
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7
        }


    # Añadir GeoJson con tooltip
    folium.GeoJson(
        gdf.__geo_interface__,
        style_function=style_function,
        tooltip=GeoJsonTooltip(
            fields=['departamen_norm', 'provincia_norm', 'nivel_pobreza'],
            aliases=['Departamento:', 'Provincia:', 'Indice de pobreza:'],
            localize=True
        )
    ).add_to(mapa)


    st.markdown("""
    <h1 style='color: #000A5C; font-family: Arial; text-align: left;'>
    🗺️ Mapa de pobreza 2025 por departamentos en Argentina 
    </h1>
    """, unsafe_allow_html=True)
    st.subheader("Si quiere obtener información sobre el censo de pobreza de un departamento especifico, presione el botón:")
    st.button("Mostrar información", key="info", on_click=change_page)
    st_folium(mapa,width=1400, height=800,key="mapa_pobreza_dep", returned_objects=[])
    # Footer con HTML y CSS

if st.session_state.page == 'mapa_dep_censal':
    st.button("Volver al mapa departamental", key="volver", on_click=volver)
    st.markdown("""
    <h1 style='color: #000A5C; font-family: Arial; text-align: left;'>
    📊 Datos de pobreza por departamento según censo 2025
    </h1>
    """, unsafe_allow_html=True)
    st.subheader("Seleccione un departamento en el mapa para ver su censo de pobreza")


