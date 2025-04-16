import streamlit as st
from app_login import login
from app_criacao_processos import criar_processo
from app_atualizacao_processos import atualizar_processo
from app_painel_visual import painel_visual
from db_connect import create_tables

# Configura a página para usar toda a largura disponível
st.set_page_config(layout="wide")

def main():
    create_tables()
    st.title("Gestão de Processos e Tarefas")

    # Se o usuário não estiver logado, exibe o formulário de login
    if 'user' not in st.session_state:
        login()
        if 'user' not in st.session_state:
            st.stop()  # Interrompe o script se não houver login

    # Botão de logout – sem uso de experimental_rerun
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state.clear()
        # Limpa a página (a página reinicia sem usuário)
        st.experimental_set_query_params(page="login")
        st.stop()

    st.sidebar.write(f"Usuário: {st.session_state.user['username']} (Nível {st.session_state.user['nivel']})")

    # Botões de navegação (cada um com key única)
    st.sidebar.markdown("### Ações")
    if st.sidebar.button("Visualizar Processos", key="btn_visualizar"):
        st.session_state.pagina = "visualizar"
    if st.sidebar.button("Criar Processo", key="btn_criar"):
        st.session_state.pagina = "criar"
    if st.sidebar.button("Atualizar Processo", key="btn_atualizar"):
        st.session_state.pagina = "atualizar"

    if 'pagina' not in st.session_state:
        st.session_state.pagina = "visualizar"

    if st.session_state.pagina == "visualizar":
        painel_visual(st.session_state.user)
    elif st.session_state.pagina == "criar":
        criar_processo()
    elif st.session_state.pagina == "atualizar":
        atualizar_processo()

if __name__ == "__main__":
    main()
