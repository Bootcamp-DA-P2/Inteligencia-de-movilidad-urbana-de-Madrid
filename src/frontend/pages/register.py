import streamlit as st

st.markdown("""
        <style>
        .main {
            background-color: #f5f7f9;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #007bff;
            color: white;
            font-weight: bold;
            border: none;
        }
        .stButton>button:hover {
            background-color: #0056b3;
            color: white;
        }
        .register-header {
            text-align: center;
            color: #1E3A8A;
            margin-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)


# Contenedor principal centrado
st.markdown("<h1 class='register-header'>🚀 TalentVector</h1>", unsafe_allow_html=True)
    
# Creamos tres columnas para centrar el formulario (proporción 1:2:1)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.container(border=True):
        st.markdown("<h2 style='text-align: center; color: #1E3A8A; margin-bottom: 1rem;'>Crear Cuenta</h2>", unsafe_allow_html=True)            
        with st.form("my_registration_form"):
            username = st.text_input("Nombre de usuario")
            name = st.text_input("Nombre")
            surname = st.text_input("Apellidos")
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            repeat_password = st.text_input("Repita la contraseña", type="password")
                
            b_col1, b_col2, b_col3 = st.columns([1,1,1])
            with b_col2:
                # El botón DEBE ser un form_submit_button
                submit_button = st.form_submit_button("Registro")
            
        if submit_button:
            # Ahora verificamos
            if username and name and surname and email and password and repeat_password:
                if repeat_password == password:
                
                    # --- CONEXIÓN CON TU API DJANGO ---
                    try:
                        with st.spinner('Autenticando...'):
                            response = register_user(email, username, name, surname, password)
                        if response.status_code == 201:
                            st.success("¡Registro completado exitosamente!")
                            st.session_state['page'] = 'login'
                            st.rerun()
                        else:
                            st.toast("Error al hacer el registro. Inténtalo de nuevo.", icon="🔥")
                                        
                    except Exception as e:
                        st.toast("Error de conexión con el servidor: {e}", icon="🔥")
                else:
                    st.warning("Las contraseñas no coinciden.")
            else:
                st.warning("Por favor, rellena todos los campos.")