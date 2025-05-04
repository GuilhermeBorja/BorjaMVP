import streamlit as st
from db_connect import get_connection
import hashlib

def hash_password(password):
    """Função para criar hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def login():
    login_container = st.container()
    with login_container:
        st.header("Login")
        username = st.text_input("Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        
        if st.button("Entrar", key="btn_entrar"):
            conn = get_connection()
            cursor = conn.cursor()
            hashed_password = hash_password(password)
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.success("Login efetuado com sucesso!")
                st.session_state.user = dict(user)
                login_container.empty()  # Limpa o formulário de login
            else:
                st.error("Usuário ou senha inválidos.")
