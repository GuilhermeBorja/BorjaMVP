import streamlit as st
from db_connect import get_connection
import datetime


def combine_date_time(date_obj, time_obj):
    return f"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}"


def criar_processo():
    st.header("Criar Novo Processo")
    col_main, col_etapas = st.columns(2)

    with col_main:
        nome_processo = st.text_input("Nome do Processo", key="cp_nome_processo")
        responsavel_geral = st.text_input("Responsável Geral", key="cp_responsavel_geral")
        etapas_quantidade = st.number_input("Quantidade de Etapas", min_value=1, step=1, value=1, key="cp_qtd_etapas")
        dt_ideal_date = st.date_input("Data de Término Ideal", key="cp_data_termino_ideal_date")
        dt_ideal_time = st.time_input("Hora de Término Ideal", key="cp_data_termino_ideal_time")
        data_termino_ideal = combine_date_time(dt_ideal_date, dt_ideal_time)
    with col_etapas:
        st.subheader("Configurar Etapas")
        etapa_nome_list = []
        etapa_resp_list = []
        for i in range(1, int(etapas_quantidade)+1):
            c1, c2 = st.columns(2)
            with c1:
                nome_etapa = st.text_input(f"Nome da Etapa {i}", key=f"cp_nome_etapa_{i}")
            with c2:
                responsavel_etapa = st.text_input(f"Responsável da Etapa {i}", key=f"cp_resp_etapa_{i}")
            etapa_nome_list.append(nome_etapa)
            etapa_resp_list.append(responsavel_etapa)

    if st.button("Salvar Processo", key="botao_salvar_processo"):
        data_criacao = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO processos (nome_processo, etapas_quantidade, responsavel_geral, data_criacao, data_termino_ideal, tempo_total, status) VALUES (?,?,?,?,?,?,?)",
            (nome_processo, etapas_quantidade, responsavel_geral, data_criacao, data_termino_ideal, "0d 0h 0m 0s", "Em andamento")
        )
        pid = cursor.lastrowid
        for name, resp in zip(etapa_nome_list, etapa_resp_list):
            cursor.execute(
                "INSERT INTO etapas (processo_id, nome_etapa, responsavel_etapa, tempo_gasto) VALUES (?,?,?,?)",
                (pid, name, resp, "0d 0h 0m 0s")
            )
        conn.commit()
        conn.close()
        st.success("Processo e etapas criados com sucesso!")
