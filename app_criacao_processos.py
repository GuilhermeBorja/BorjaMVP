import streamlit as st
from db_connect import get_connection
import datetime

def criar_processo():
    st.header("Criar Novo Processo")
    # Divide a tela em duas colunas para aproveitar a largura
    col_main, col_etapas = st.columns(2)

    with col_main:
        nome_processo = st.text_input("Nome do Processo", key="cp_nome_processo")
        responsavel_geral = st.text_input("Responsável Geral", key="cp_responsavel_geral")
        etapas_quantidade = st.number_input("Quantidade de Etapas", min_value=1, step=1, value=1, key="cp_qtd_etapas")
        data_termino_ideal = st.date_input("Data de Término Ideal", key="cp_data_termino_ideal")
    with col_etapas:
        st.subheader("Configurar Etapas")
        etapa_nome_list = []
        etapa_resp_list = []
        # Utiliza uma coluna interna para agrupar os campos horizontalmente
        for i in range(1, int(etapas_quantidade)+1):
            cols = st.columns(2)
            with cols[0]:
                nome_etapa = st.text_input(f"Nome da Etapa {i}", key=f"cp_nome_etapa_{i}")
            with cols[1]:
                responsavel_etapa = st.text_input(f"Responsável da Etapa {i}", key=f"cp_resp_etapa_{i}")
            etapa_nome_list.append(nome_etapa)
            etapa_resp_list.append(responsavel_etapa)

    if st.button("Salvar Processo", key="botao_salvar_processo"):
        data_criacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO processos (nome_processo, etapas_quantidade, responsavel_geral, data_criacao, data_termino_ideal, tempo_total, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                nome_processo,
                int(etapas_quantidade),
                responsavel_geral,
                data_criacao,
                data_termino_ideal.strftime("%Y-%m-%d"),
                0,
                "No prazo"
            )
        )
        processo_id = cursor.lastrowid
        for i in range(len(etapa_nome_list)):
            nome_etapa = etapa_nome_list[i]
            responsavel_etapa = etapa_resp_list[i]
            if nome_etapa and responsavel_etapa:
                cursor.execute(
                    '''INSERT INTO etapas (processo_id, nome_etapa, responsavel_etapa, tempo_gasto)
                       VALUES (?, ?, ?, ?)''',
                    (processo_id, nome_etapa, responsavel_etapa, 0)
                )
        conn.commit()
        conn.close()
        st.success("Processo e suas etapas criados com sucesso!")
