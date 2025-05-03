import streamlit as st
from app_login import login
from app_criacao_processos import criar_processo
from app_atualizacao_processos import atualizar_processo
from app_painel_visual import painel_visual
from db_connect import create_tables

# 1) layout wide
st.set_page_config(layout="wide")
# 2) CSS p/ botão apagar não quebrar
st.markdown("""
    <style>
      button[data-baseweb="button"] { white-space: nowrap; }
    </style>
""", unsafe_allow_html=True)
# 3) captura timezone offset do navegador
st.markdown("""
  <script>
    const tz = new Date().getTimezoneOffset();
    window.parent.postMessage({ type: 'TZ_OFFSET', offset: tz }, '*');
  </script>
""", unsafe_allow_html=True)

# listener para TZ_OFFSET
def _receive_tz():
    msg = st.experimental_data_editor.key   # hack: disparar rerun
for event in st.session_state.get('_streamlit_events', []):
    if isinstance(event, dict) and event.get('type')=='TZ_OFFSET':
        st.session_state.tz_offset = int(event['offset'])
st.session_state.setdefault('tz_offset', 0)

def main():
    create_tables()
    st.title("Gestão de Processos e Tarefas")

    # login
    if 'user' not in st.session_state:
        login()
        if 'user' not in st.session_state:
            return
        st.session_state.pagina = "visualizar"
        st.rerun()  # Force a rerun to show the visualizar page immediately

    # logout
    if st.sidebar.button("Logout"):
        # Clear all session state variables
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()  # Force a rerun to return to login page
        return

    st.sidebar.write(f"Usuário: {st.session_state.user['username']} (Nível {st.session_state.user['nivel']})")
    st.sidebar.markdown("### Ações")
    if st.sidebar.button("Visualizar Processos"): st.session_state.pagina="visualizar"
    if st.sidebar.button("Criar Processo"): st.session_state.pagina="criar"
    if st.sidebar.button("Atualizar Processo"): st.session_state.pagina="atualizar"

    if st.session_state.pagina=="visualizar":
        painel_visual(st.session_state.user)
    elif st.session_state.pagina=="criar":
        criar_processo()
    else:
        atualizar_processo()

if __name__=="__main__":
    main()
