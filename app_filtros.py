import streamlit as st
import datetime
from db_connect import get_connection


def filtros_processos():
    st.sidebar.subheader("Filtros Avançados")
    nome = st.sidebar.text_input("Nome do Processo")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT responsavel_geral FROM processos")
    reps = [r['responsavel_geral'] for r in cur.fetchall() if r['responsavel_geral']]
    conn.close()
    reps.insert(0, "Todos")
    responsavel = st.sidebar.selectbox("Responsável Geral", reps)
    status = st.sidebar.selectbox("Status", ["Todos", "Em andamento", "No prazo", "Atrasado", "Concluído"])
    st.sidebar.markdown("### Data de Criação")
    c1, c2 = st.sidebar.columns(2)
    with c1: di = st.date_input("Início", datetime.date.today())
    with c2: df = st.date_input("Fim",    datetime.date.today())
    return {"data_inicio": di, "data_fim": df, "nome": nome, "responsavel": responsavel, "status": status}
