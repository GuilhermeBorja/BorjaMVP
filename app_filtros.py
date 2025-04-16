import streamlit as st
import datetime
from db_connect import get_connection

def filtros_processos():
    st.sidebar.subheader("Filtros Avançados")
    
    filtro_nome = st.sidebar.text_input("Nome do Processo", key="filtro_nome")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT responsavel_geral FROM processos")
    responsaveis = [row["responsavel_geral"] for row in cursor.fetchall() if row["responsavel_geral"]]
    conn.close()
    responsaveis.insert(0, "Todos")
    filtro_responsavel = st.sidebar.selectbox("Responsável Geral", options=responsaveis, key="filtro_responsavel")
    
    filtro_status = st.sidebar.selectbox("Status", options=["Todos", "No prazo", "Atrasado", "Finalizado no prazo", "Finalizado atrasado"], key="filtro_status")
    
    st.sidebar.markdown("### Data de Criação")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.date_input("Início", datetime.date.today(), key="filtro_data_inicio")
    with col2:
        data_fim = st.date_input("Fim", datetime.date.today(), key="filtro_data_fim")
    
    return {
        "nome": filtro_nome,
        "responsavel": filtro_responsavel,
        "status": filtro_status,
        "data_inicio": data_inicio,
        "data_fim": data_fim
    }
