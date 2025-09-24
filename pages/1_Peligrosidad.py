import geopandas as gpd
import pandas as pd
import unicodedata
import folium
from folium.features import GeoJson, GeoJsonTooltip
import branca.colormap as cm
import streamlit as st
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(page_title="Robos y hurtos en argentina", layout='wide')

st.markdown("""
<style>
.stSelectbox {
    width: 200px; /* Cambia este valor al ancho que desees */
}
</style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'mapa_peligrosidad'
def change_page():
    if(st.session_state.page == 'grafico_estadist'):
        st.session_state.page = 'mapa_peligrosidad'
    elif(st.session_state.page == 'mapa_peligrosidad'):
        st.session_state.page = 'grafico_estadist'

if st.session_state.page == 'mapa_peligrosidad':

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

    st.markdown("""
    <h1 style='color: #333333; font-family: Calibri; text-align: left; font-size: 31px;'>
    🗺️ Mapa dinámico de robos y hurtos por año
    </h1>
    """, unsafe_allow_html=True)

    anios = list(df_robos_hurtos_sumados['anio'].unique())
    anio_seleccionado = st.selectbox(
        "Selecciona un año:",
        options=anios, # Reemplaza con tus años
        index=0
    )

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
        zoom_start=5
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
    #Mostramos el mapa
    st.subheader(f"**Año seleccionado:** {anio_seleccionado}")
    st_folium(mapa,width=1400, height=800, key="mapa_delitos", returned_objects=[])

    st.subheader("También contamos con graficos estadísticos sobre los delitos por provincia, si quiere mas informacion pulse aqui abajo")
    st.button("Ver graficos estadísticos", on_click=change_page)

if st.session_state.page == 'grafico_estadist':
    
    @st.cache_data
    def load_data():
        return pd.read_csv("csv/snic-departamentos-anual.csv", sep=';', encoding='utf-8', low_memory=False)

    df = load_data()
    
    st.markdown(
        """ 
            <style>
            .st-emotion-cache-ig7yu6{
                background-color: #F0F0F0 !important;
                border-radius: 10px !important;
                
            }
            .st-emotion-cache-wfksaw{
                margin: 10px !important;
                width: 95% !important;
            }
            
            </style>
        """,unsafe_allow_html=True
    )

    st.markdown("""
    <h1 style='color: #333333; font-family: Calibri; text-align: left; font-size: 31px;'>
    📈 Gráfico estadistico de peligrosidad
    </h1>
    """, unsafe_allow_html=True)
    #Seleccionamos la provincia
    provincias = df['provincia_nombre'].drop_duplicates()
    provincia_seleccionada = st.selectbox(
        "Seleccione una provincia: ",
        provincias
    )
    #Filtramos el dataframe
    df = df[df['cod_delito'].isin([15, 16, 19, 20])]
    df = df.loc[df['provincia_nombre'] == provincia_seleccionada].copy()
    df = df.groupby(['anio'], as_index=False)['cantidad_hechos'].sum()
    
    #Creamos columnas en streamlit
    col1, col2 = st.columns([4,1])
    #Creamos la x e y en el grafico
    anios = df['anio'].unique()
    x_data = df['anio']
    y_data = df['cantidad_hechos']

    año_mas_delitos = df.loc[df['cantidad_hechos'].idxmax()]['anio']
    cantidad_maximo_delitos = df.loc[df['cantidad_hechos'].idxmax()]['cantidad_hechos']
    with col1:
        #Creamos el grafico, necesitamos crearlo con 2 variables, fig y ax, fig
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.plot(x_data, y_data)
        ax.set_title(f'Cantidad de robos y hurtos en {provincia_seleccionada}')
        ax.set_xticks(anios)
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlabel('Años')
        ax.set_ylabel('Cantidad de robos/hurtos')
        fig.tight_layout()
        
        st.pyplot(fig)
    with col2:
        st.header('Información estadística')
        st.markdown(
            f"Año con mayores robos/hurtos en la provincia de {provincia_seleccionada}: **{año_mas_delitos}**"
        )
        st.markdown(
            f"Mayor cantidad de robos/hurtos en la provincia de {provincia_seleccionada}: **{cantidad_maximo_delitos}**"
        )
        
        
        

    
    

    


    
    


