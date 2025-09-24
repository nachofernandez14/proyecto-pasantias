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
    df_pobreza.to_csv('csv/df_pobreza_dep.csv', index=False)
    #Creamos el mapa
    mapa = folium.Map(location=[-38.0, -63.0], zoom_start=5)


    #Muy bajo, Bajo, Moderado, Alto, Muy alto, Crítico
    colores = ['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027']
    #Funcion para determinar por colores los indices de la pobreza de cada dep
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
    <h1 style='color: #333333; font-family: Calibri; text-align: left; font-size: 31px;'>
    🗺️ Mapa de pobreza 2025 por departamentos en Argentina 
    </h1>
    """, unsafe_allow_html=True)
    st_folium(mapa,width=1400, height=800,key="mapa_pobreza_dep", returned_objects=[])
    st.subheader("Si quiere obtener información sobre el censo de pobreza de una provincia mas a fondo, presione el botón:")
    st.button("Censo pobreza provincial", key="info", on_click=change_page)
    

if st.session_state.page == 'mapa_dep_censal':
    st.markdown("""
        <style>
        .stSelectbox {
            width: 200px; /* Cambia este valor al ancho que desees */
        }
        </style>
    """, unsafe_allow_html=True)
    st.button("Volver al mapa departamental", key="volver", on_click=volver)
    st.markdown("""
    <h1 style='color: #333333; font-family: Calibri; text-align: left; font-size: 31px;'>
    📊 Datos de pobreza por provincia (zona censal) según censo 2025
    </h1>
    """, unsafe_allow_html=True)

    st.subheader("Seleccione una provincia para ver su censo de pobreza")
    
    gdf = gpd.read_file('shp_radio_censal/radios2022_v1.0.shp')

    provincias = gdf['NOMPROV'].drop_duplicates()
    #Sacamos caba y buenos aires para arreglarlos
    provincias = provincias[~provincias.isin(['CABA', 'BUENOS AIRES'])]
    provincia_seleccionada = st.selectbox(
        "Seleccione una provincia: ",
        provincias
    )
    gdf_provincia = gdf.loc[gdf['NOMPROV'] == provincia_seleccionada].copy()
    #Calcular el centroide donde se va a posicionar el mapa dependiendo de la provincia
    center_lat = gdf_provincia.geometry.union_all().centroid.y
    center_lon = gdf_provincia.geometry.union_all().centroid.x

    df_1 = pd.read_csv('csv/RADIOS SHEET FINAL_data.csv', encoding='utf-8', sep=';')

    df_pobreza_radial = df_1[['Código de radio','Departamento','Nivel de incidencia de pobreza crónica', 'Provincia']]

    df_pobreza_radial = df_pobreza_radial.rename(columns={
        'Código de radio': 'radio_codigo',
        'Departamento': 'departamento_nombre',
        'Nivel de incidencia de pobreza crónica': 'pobreza_cronica_nivel',
        'Provincia': 'provincia_nombre'
    })
    #FUNCION PARA NORMALIZAR TEXTOS
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

    #NORMALIZAMOS
    df_pobreza_radial['departament_norm'] = df_pobreza_radial['departamento_nombre'].apply(normalizar_textos)
    df_pobreza_radial['provincia_nombre'] = df_pobreza_radial['provincia_nombre'].apply(normalizar_textos)
    gdf_provincia['provincia_norm'] = gdf_provincia['NOMPROV'].apply(normalizar_textos)

    correcciones_bsas = {
        'partidos del agba': 'buenos aires',
        'ciudad de buenos aires': 'caba',
        'buenos aires (sin agba)': 'buenos aires',
        'provincia de buenos aires': 'buenos aires',
        'provincia de buenos aires (sin agba)': 'buenos aires',
        'ciudad autonoma de buenos aires': 'caba'
    }
    df_pobreza_radial['provincia_nombre'] = df_pobreza_radial['provincia_nombre'].replace(correcciones_bsas)
    gdf_provincia['provincia_norm'] = gdf_provincia['provincia_norm'].replace(correcciones_bsas)

    #PASAMOS LOS CODIGOS CENSALES A STRING
    gdf_provincia['LINK'] = gdf_provincia['LINK'].astype(str)
    df_pobreza_radial['radio_codigo'] = df_pobreza_radial['radio_codigo'].astype(str)
    
    gdf_provincia['LINK'] = gdf_provincia['LINK'].str.lstrip('0')

    gdf_provincia = gdf_provincia.merge(
        df_pobreza_radial,
        left_on=['LINK', 'provincia_norm'],
        right_on=['radio_codigo', 'provincia_nombre'],
        how='left'
    )

    mapeo_pobreza = {
        'Muy bajo (0 - 0,99%)': 0.5,
        'Bajo (1 - 4,99%)': 3.0,
        'Moderado (5 - 9,99%)': 7.5,
        'Alto (10 - 14,99%)': 12.5,
        'Muy alto (15 - 24,99%)': 20.0,
        'Crítico (25 - 100%)': 37.5
    }
    gdf_provincia['pobreza_cronica_nivel'] = gdf_provincia['pobreza_cronica_nivel'].map(mapeo_pobreza)
    df_pobreza_radial['pobreza_cronica_nivel'] = df_pobreza_radial['pobreza_cronica_nivel'].map(mapeo_pobreza)

    mapa = folium.Map(location=[center_lat,center_lon], zoom_start=5)

    colores = ['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027']

    def style_function(pobreza):
        cant_pobreza = pobreza['properties'].get('pobreza_cronica_nivel')
        if cant_pobreza is None:
            return {'fillColor': '#808080', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
        try:
            cant_pobreza=float(cant_pobreza)
        except (ValueError, TypeError):
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
    folium.GeoJson(
        gdf_provincia.__geo_interface__,
        style_function=style_function,
        tooltip=GeoJsonTooltip(
            fields=['LINK', 'provincia_norm','departament_norm', 'pobreza_cronica_nivel'],
            aliases=['Codigo censal:', 'Provincia:', 'Departamento:', 'Indice de pobreza:'],
            localize=True
        )
    ).add_to(mapa)
    st.markdown("***La provincia de Buenos Aires está en mantenimiento***")
    st_folium(mapa,width=1400, height=800,key="mapa_pobreza_dep", returned_objects=[])

    