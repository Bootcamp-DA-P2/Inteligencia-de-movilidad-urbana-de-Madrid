import streamlit as st
from services.auth_service import login_user


def show_login_page():
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
        .login-header {
            text-align: center;
            color: #1E3A8A;
            margin-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)


    # Contenedor principal centrado
    st.markdown("<h1 class='login-header'>🚀 MadFlow</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.container(border=True):
            st.subheader("Iniciar Sesión")
            
            email = st.text_input("Correo electrónico", placeholder="ejemplo@correo.com")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            
            st.markdown("---")

            b_col1, b_col2, b_col3 = st.columns([1,0.75,1])
            with b_col2:
                btn_login = st.button("Login")
            
            if btn_login:
                if email and password:
                    
                    try:
                        with st.spinner('Autenticando...'):
                            response = login_user(email, password)
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.clear()
                            # Guardamos los tokens en la sesión de Streamlit
                            st.session_state['logged_in'] = True
                            st.session_state["user_data"] = data.get("user", {})
                            
                            st.success(f"¡Bienvenido, {data['user']['name']}!")
                            # Aquí podrías usar st.rerun() para ir a la página principal
                            st.session_state['page'] = 'home'
                            st.rerun()
                        else:
                            st.toast("Credenciales incorrectas. Inténtalo de nuevo.")
                            
                    except Exception as e:
                        st.error(f"Error de conexión con el servidor: {e}")
                else:
                    st.toast("Por favor, rellena todos los campos.")

            st.write("")

            c_col1, c_col2, c_col3 = st.columns([1,4,1])

            with c_col2:
                btn_register = st.button("¿No tienes cuenta? Regístrate", key="btn_reg")

            if btn_register:
                st.session_state['page'] = 'register'
                st.rerun()