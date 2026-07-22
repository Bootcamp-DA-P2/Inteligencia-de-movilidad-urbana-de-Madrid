import streamlit as st

from theme import apply_theme, header_banner
apply_theme()
header_banner("MadFlow: Sobre Nosotros", "El equipo detrás del proyecto")

def card_user(user):
    img = user.get('img', '')
    name = str(user.get('name', ''))
    info = user.get('info', '')

    st.markdown(
        f"""
        <div style="
            background-color: white;
            padding: 25px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            display: flex;
            flex-direction: column;
            font-family: 'Open Sans', sans-serif;
            margin-bottom: 20px;
            height: 250px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="
                    min-width: 80px;
                    height: 80px;
                    border: 1px solid #f0f0f0;
                    border-radius: 50%; /* Cambiado a círculo para fotos de equipo */
                    overflow: hidden;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 16px;
                    background-color: #fafafa;
                ">
                    <img src="{img}" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                <div style="flex-grow: 1;">
                    <h3 style="margin: 0; font-size: 20px; color: #111; font-weight: 700;">
                        {name}
                    </h3>
                </div>
            </div>
            <div style="font-size: 14px; color: #555; line-height: 1.5; padding-top: 5px;">
                {info.capitalize()}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.title("👨‍💻 Quiénes Somos")
st.markdown("---")

# --- DATOS DEL EQUIPO ---
# (Asegúrate de poner fotos reales o avatars en tu carpeta 'public')
equipo = [
    {
        "name": "Pepe",
        "info": "lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "img": "https://th.bing.com/th/id/R.b2b34517339101a111716be1c203f354?rik=e5WHTShSpipi3Q&pid=ImgRaw&r=0"
    },
    {
        "name": "Pepa",
        "info": "lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "img": "https://th.bing.com/th/id/R.b2b34517339101a111716be1c203f354?rik=e5WHTShSpipi3Q&pid=ImgRaw&r=0"
    },
    {
        "name": "Juan",
        "info": "lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",  
        "img": "https://th.bing.com/th/id/R.b2b34517339101a111716be1c203f354?rik=e5WHTShSpipi3Q&pid=ImgRaw&r=0"
    },
    {
        "name": "Ana",
        "info": "lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "img": "https://th.bing.com/th/id/R.b2b34517339101a111716be1c203f354?rik=e5WHTShSpipi3Q&pid=ImgRaw&r=0"
    },
    {
        "name": "Pedro",
        "info": "lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "img": "https://th.bing.com/th/id/R.b2b34517339101a111716be1c203f354?rik=e5WHTShSpipi3Q&pid=ImgRaw&r=0"
    }
]

# --- RENDERIZADO EN GRID (2 columnas) ---
# Usamos columnas nativas de Streamlit para que las tarjetas se posicionen lado a lado de forma responsiva
col1, col2 = st.columns(2)

for i, integrante in enumerate(equipo):
    if i % 2 == 0:
        with col1:
            card_user(integrante)
    else:
        with col2:
            card_user(integrante)

st.markdown("---")
st.caption("© 2026 Inteligencia de Movilidad Urbana de Madrid. Desarrollado con ❤️ para una ciudad más sostenible.")