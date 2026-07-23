import streamlit as st
from groq import Groq
from utils import load_config

client = Groq(api_key=load_config()['GROQ_API_KEY'])

st.session_state.messages = [
    {"role": "system", "content": "Eres un asistente experto en movilidad urbana en Madrid. Proporciona información precisa y útil sobre rutas, transporte público, tráfico y cualquier otro aspecto relacionado con la movilidad en la ciudad. Mantén un tono profesional y amigable."}
]

# Inicialización del estado de la sesión para almacenar la respuesta del modelo
if 'response' not in st.session_state:
    st.session_state.response = '¡Hola! Soy tu asesor movilístico. ¿En qué puedo ayudarte?'

# Configuración de la página
st.set_page_config(page_title="MadBot", page_icon="")

st.title('MAD-Bot')
st.markdown("Optimiza tu ruta de desplazamiento en Madrid")

user_input = st.chat_input("Quiero ir a Valdebebas desde ...")

# 4. Lógica de procesamiento (Solo si hay input real)
if user_input: # Esto filtra None y strings vacíos automáticamente
    # Añadimos el mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.spinner("Generando respuesta..."):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                # Enviamos todo el historial para que tenga contexto
                messages=st.session_state.messages,
            )

            answer = completion.choices[0].message.content
            st.session_state.response = answer
            # Añadimos la respuesta al historial para mantener el contexto
            st.session_state.messages.append({"role": "assistant", "content": answer})
        
        except Exception as e:
            st.error(f"Error al conectar con Groq: {e}")

# 5. Visualización de la respuesta
# Usamos un contenedor para que el formato sea limpio
formatted_response = st.session_state.response.replace('\n', '<br>')
st.markdown(
    f"""
    <div style="background-color:#f6f6f6; border-radius:10px; padding:20px; margin-top:20px; border:1px solid #e3e3e3; color: #111;">
    <b>Chatbot:</b><br>
    {formatted_response}
    </div>
    """,
    unsafe_allow_html=True
)