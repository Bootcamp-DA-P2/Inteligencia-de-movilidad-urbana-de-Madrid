import requests
import streamlit as st
from utils import load_config

url_auth= load_config()['URL_AUTH']

def login_user(email, password):
    response = requests.post(url_auth + "login/", json={
                    "email": email,
                    "password": password
                })
    return response

def register_user(email, username, name, surname, password):
    response = requests.post(url_auth + "register/", json={
                    "email": email,
                    "username": username,
                    "name": name,
                    "surname": surname,
                    "password": password
                })
    return response

def get_user_profile(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url_auth + "profile/", headers=headers)
    return response

def logout():
    st.session_state.clear()
    
    st.session_state["access"] = None
    st.session_state["logged_in"] = False
    st.session_state["page"] = "login"
    st.rerun()