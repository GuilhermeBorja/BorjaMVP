import streamlit as st
from db_connect import get_connection


def login():
    container = st.container()
    with container:
        st.header("Login")
        user = st.text_input("Usuário", key="login_username")
        pwd = st.text_input("Senha", type="password", key="login_password")
        if st.button("Entrar", key="btn_entrar"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
            record = cur.fetchone()
            conn.close()
            if record:
                st.success("Login bem‑sucedido!")
                st.session_state.user = dict(record)
                container.empty()
            else:
                st.error("Usuário ou senha inválidos.")
