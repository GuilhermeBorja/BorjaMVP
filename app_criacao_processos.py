import streamlit as st
from db_connect import get_connection
import datetime

def combine_date_time(date_obj, time_obj):
    return f"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}"

def criar_processo():
    st.header("Criar Novo Processo")
    c1, c2 = st.columns(2)

    with c1:
        nome = st.text_input("Nome do Processo", key="cp_nome")
        resp = st.text_input("Responsável Geral", key="cp_resp")
        qtd = st.number_input("Quantidade de Etapas", min_value=1, step=1, value=1, key="cp_qtd")
        d = st.date_input("Data de Término Ideal", key="cp_date")
        t = st.time_input("Hora de Término Ideal", key="cp_time")
        termo_ideal = combine_date_time(d, t)

    with c2:
        st.subheader("Configurar Etapas")
        etapas_nome = []
        etapas_resp = []
        for i in range(qtd):
            ne = st.text_input(f"Nome da Etapa {i+1}", key=f"cp_ne_{i}")
            re = st.text_input(f"Responsável da Etapa {i+1}", key=f"cp_re_{i}")
            etapas_nome.append(ne)
            etapas_resp.append(re)

    if st.button("Salvar Processo", key="cp_save"):
        cri = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        conn = get_connection(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO processos (nome_processo, etapas_quantidade, responsavel_geral, data_criacao, data_termino_ideal, tempo_total, status) VALUES (?,?,?,?,?,?,?)",
            (nome, qtd, resp, cri, termo_ideal, "0d 0h 0m 0s", "Em andamento")
        )
        pid = cur.lastrowid
        for ne, re in zip(etapas_nome, etapas_resp):
            cur.execute(
                "INSERT INTO etapas (processo_id, nome_etapa, responsavel_etapa, tempo_gasto) VALUES (?,?,?,?)",
                (pid, ne, re, "0d 0h 0m 0s")
            )
        conn.commit(); conn.close()
        st.success("Processo criado com sucesso!")
