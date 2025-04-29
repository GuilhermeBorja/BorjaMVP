import streamlit as st
from app_login import login
from app_criacao_processos import criar_processo
from app_atualizacao_processos import atualizar_processo
from app_painel_visual import painel_visual
from db_connect import create_tables

# Chamado apenas uma vez, antes de qualquer outro comando Streamlit
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 200px; max-width: 400px; }
    [data-testid="stSidebarNav"] { width: 250px; }
    </style>
""", unsafe_allow_html=True)

def main():
    create_tables()
    st.title("Gestão de Processos e Tarefas")

    if 'user' not in st.session_state:
        login()
        if 'user' not in st.session_state:
            return
        st.session_state.pagina = "visualizar"

    if st.sidebar.button("Logout", key="logout"):
        st.session_state.clear()
        st.set_query_params(page="login")
        return

    st.sidebar.write(f"Usuário: {st.session_state.user['username']} (Nível {st.session_state.user['nivel']})")
    st.sidebar.markdown("### Ações")
    if st.sidebar.button("Visualizar Processos", key="nav_viz"): st.session_state.pagina = "visualizar"
    if st.sidebar.button("Criar Processo", key="nav_criar"): st.session_state.pagina = "criar"
    if st.sidebar.button("Atualizar Processo", key="nav_atualizar"): st.session_state.pagina = "atualizar"

    if st.session_state.pagina == "visualizar":
        painel_visual(st.session_state.user)
    elif st.session_state.pagina == "criar":
        criar_processo()
    elif st.session_state.pagina == "atualizar":
        atualizar_processo()

if __name__ == "__main__":
    main()
