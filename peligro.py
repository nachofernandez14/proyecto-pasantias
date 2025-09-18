import geopandas as gpd
import pandas as pd
import unicodedata
import folium
from folium.features import GeoJson, GeoJsonTooltip
import branca.colormap as cm
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Robos y hurtos en argentina", layout='wide')

st.markdown(
    """
    <style>
    .reportview-container .main .block-container{
        padding-top: 5rem;
        padding-right: 5rem;
        padding-left: 5rem;
        padding-bottom: 5rem;
    }
    .reportview-container .main {
        color: #555;
        background-color: #f0f2f6;
    }
    .css-1d3f9p6 {
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    .footer {
        width: 100%;
        background-color: #f0f2f6;
        text-align: center;
        padding: 10px 0;
        font-size: 14px;
        color: #555;
        position: fixed;
        bottom: 0;
        left: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_data():
    return pd.read_csv("csv/snic-departamentos-anual.csv", sep=';', encoding='utf-8', low_memory=False)

df = load_data()


#DEPARTAMENTOS CON MAS ROBOS Y HURTOS
codigos_delitos = [15, 16, 19, 20]
df_robos_hurtos = df[df['cod_delito'].isin(codigos_delitos)]

#SUMAMOS LOS HECHOS POR DEPARTAMENTO
df_robos_hurtos_sumados = (
    df_robos_hurtos
    .groupby(['departamento_nombre','provincia_nombre','anio'], as_index=False)['cantidad_hechos']
    .sum()
    )

df_deptos_unicos = df_robos_hurtos[['departamento_nombre', 'provincia_nombre', 'departamento_id', 'provincia_id']].drop_duplicates()

df_robos_hurtos_sumados = df_robos_hurtos_sumados.merge(
    df_deptos_unicos[['departamento_nombre','provincia_nombre']].drop_duplicates(),
    on=['departamento_nombre', 'provincia_nombre'],
    how='left'
)



#Funcion para normalizar los textos y eliminar espacios, tildes y dejar todo en mayusc
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

#Cargamos el mapa
gdf = gpd.read_file("departamentos/pxdptodatosok.shp")

#Normalizamos los departamentos y provincias del dataframe y del gdf
gdf["departamen_norm"] = gdf["departamen"].apply(normalizar_textos)
gdf['provincia_norm'] = gdf['provincia'].apply(normalizar_textos)
df_robos_hurtos_sumados["departamento_nombre"] = df_robos_hurtos_sumados['departamento_nombre'].apply(normalizar_textos)
df_robos_hurtos_sumados["provincia_nombre"] = df_robos_hurtos_sumados['provincia_nombre'].apply(normalizar_textos)

años = list(df['anio'].unique())
anio_seleccionado = st.sidebar.selectbox("Seleccione un año", años)

#Filtramos el dataframe por un año
df_robos_hurtos_sumados = df_robos_hurtos_sumados[df_robos_hurtos_sumados['anio'] == anio_seleccionado]



#Mergeamos el gdf con el data frame, haciendo coincidir los departamentos con las provincias
gdf = gdf.merge(
    df_robos_hurtos_sumados, 
    left_on=['departamen_norm' ,'provincia_norm'], 
    right_on=['departamento_nombre', 'provincia_nombre'], 
    how='left')

#Cargamos los reemplazos que no se aplicaron con el merge
reemplazos = {
    "coronel felipe varela": "general felipe varela",
    "general angel v. penaloza": "angel vicente penaloza",
    "coronel de marina l. rosales": "coronel de marina leonardo rosales",
    "quemu ouemu": "quemu quemu",
    "chicalco": "chical co",
    "o' higgins": "o'higgins",
    "grl. jose de san martin": "general jose de san martin",
    "juan f. ibarra": "juan felipe ibarra",
    "1º de mayo": "1° de mayo",
    "juan f. quiroga": "general juan facundo quiroga",
    "libertador grl. san martin": "libertador general san martin",
    # Los que no tienen geometría real:
    "departamento sin determinar": None,
    "norte (general pico)": None,
    "sur (general acha)": None,
    "centro (santa rosa)": None,
    "oeste (25 de mayo)": None
}

#Reemplazamos los nulos por cantidad 0
gdf['cantidad_hechos'] = gdf['cantidad_hechos'].fillna(0)

# Aplicar reemplazos en tu df
df_robos_hurtos_sumados['departamento_nombre'] = (
    df_robos_hurtos_sumados['departamento_nombre'].replace(reemplazos)
)


# Quitar los None porque no tienen match geográfico
df_robos_hurtos_sumados = df_robos_hurtos_sumados.dropna(subset=['departamento_nombre'])


# # Generamos un mapa con el numero de delitos por departamento
#Creamos el mapa
mapa = folium.Map(
    location=[-38.0, -63.0], 
    zoom_start=5,
    tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png',
    attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
    )
#Creamos el colormap
colormap = cm.linear.YlOrRd_09.scale(
    gdf['cantidad_hechos'].min(),
    gdf['cantidad_hechos'].max()
)
colormap.caption = 'Cantidad de delitos'

#Funcion para colorear por cantidad de hechos
def style_function(feature):
    cantidad = feature['properties'].get('cantidad_hechos', 0)
    return {
        'fillColor': colormap(cantidad),
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7
    }

# Añadir GeoJson con tooltip
folium.GeoJson(
    gdf.__geo_interface__,
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=['departamen_norm', 'cantidad_hechos', 'provincia_norm'],
        aliases=['Departamento:', 'Delitos:', 'Provincia:'],
        localize=True,
        sticky=True,
        labels=True,
        style="""
            background-color: #FFFFFF;
            border: 1px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """
    )
).add_to(mapa)

# Añadir leyenda
colormap.add_to(mapa)


st.markdown("""
<h1 style='color: #000A5C; font-family: Arial; text-align: left;'>
   🗺️ Mapa dinámico de robos y hurtos por año
</h1>
""", unsafe_allow_html=True)
st.subheader(f"**Año seleccionado:** {anio_seleccionado}")
st_folium(mapa, width=1300, height=650, key="mapa_delitos", returned_objects=[])
# Footer con HTML y CSS

st.markdown(
    """
    <div class="footer">
        © 2025 Ignacio Fernandez - Todos los derechos reservados
        <br>
        <a href="https://github.com/ignacio-fernandez" target="_blank">GitHub</a>
        <br>
        <a href="https://www.argentina.gob.ar/seguridad/estadisticascriminales/bases-de-datos" target="_blank">Fuente de los datos obtenidos para realizar los mapas</a>
    </div>
    """,
    unsafe_allow_html=True
)

