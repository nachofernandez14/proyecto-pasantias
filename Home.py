import streamlit as st

st.set_page_config(page_title="Inicio", layout='wide')

st.title("Bienvenido a la Aplicación de Análisis de Datos en Argentina")

st.markdown(
    """
    <style>
    @media (min-width: calc(736px + 8rem)) {
    .st-emotion-cache-zy6yx3 {
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    </style>
    """,unsafe_allow_html=True
)

st.markdown("""
Esta aplicación interactiva te permite explorar la distribución de robos y hurtos, analizar datos de pobreza y visualizar otros indicadores sociales en el país.

**Usa el menú de la izquierda para navegar entre las diferentes secciones:**
* **🗺️ Mapa de Peligrosidad:** Explora los datos de delitos geolocalizados por año.
* **📊 Análisis de Pobreza:** Observa las estadísticas de pobreza por región.

---
""")

# Sección de créditos
st.subheader("Acerca de esta aplicación")
st.info("""
**Desarrollado por:** Ignacio Fernandez 
        
**Tutor:** Facundo Mendez 
        
**Año:** 2025 
        
**Fuente de los datos:**     
[Ministerio de Seguridad de la Nación](https://www.argentina.gob.ar/seguridad/estadisticascriminales/bases-de-datos)      
[Ministerio de Defensa CAPAS SIG](https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/CapasSIG)   
[CIPEC](https://www.cippec.org/)     
[Datos Abietos PBA](https://catalogo.datos.gba.gob.ar/dataset/radios-censales/archivo)
        
""")
