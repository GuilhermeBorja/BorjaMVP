import streamlit as st
from db_connect import get_connection

def login():
    container = st.container()
    with container:
        st.header("Login")
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pwd")
        if st.button("Entrar", key="login_btn"):
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cur.fetchone()
            conn.close()
            if user:
                st.success("Login bem-sucedido!")
                st.session_state.user = dict(user)
                container.empty()
            else:
                st.error("Usuário ou senha inválidos.")
