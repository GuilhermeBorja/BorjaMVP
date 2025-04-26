import streamlit as st
from db_connect import get_connection
import datetime

# Helper para combinar data e hora no formato brasileiro sem segundos
def combine_date_time(date_obj, time_obj):
    return f"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}"

# Função principal para atualizar processos
def atualizar_processo():
    st.header("Atualizar Processo")

    # Busca lista de processos
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_processo FROM processos")
    processos = cursor.fetchall()
    conn.close()

    if not processos:
        st.info("Nenhum processo cadastrado para atualizar.")
        return

    # Seleção do processo por nome
    processos_dict = {p['nome_processo']: p['id'] for p in processos}
    selected = st.selectbox(
        "Selecione o Processo (por Nome)",
        options=list(processos_dict.keys()),
        key="upd_select_processo"
    )

    if selected:
        processo_id = processos_dict[selected]

        # Carrega dados do processo e suas etapas
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processos WHERE id=?", (processo_id,))
        processo = cursor.fetchone()
        cursor.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (processo_id,))
        etapas = cursor.fetchall()
        conn.close()

        st.subheader("Dados do Processo")
        # Campos editáveis pré-preenchidos
        novo_nome = st.text_input(
            "Nome do Processo", value=processo['nome_processo'], key="upd_nome_processo"
        )
        novo_resp_geral = st.text_input(
            "Responsável Geral", value=processo['responsavel_geral'], key="upd_resp_geral"
        )

        # Seletor de data/hora para Data de Término Ideal
        try:
            dt_ideal = datetime.datetime.strptime(processo['data_termino_ideal'], "%d/%m/%Y %H:%M")
        except:
            dt_ideal = datetime.datetime.now()
        novo_dt_ideal_date = st.date_input(
            "Data de Término Ideal", value=dt_ideal.date(), key="upd_dt_ideal_date"
        )
        novo_dt_ideal_time = st.time_input(
            "Hora de Término Ideal", value=dt_ideal.time(), key="upd_dt_ideal_time"
        )
        novo_data_term_ideal = combine_date_time(novo_dt_ideal_date, novo_dt_ideal_time)

        st.subheader("Campos Não Editáveis")
        st.text_input(
            "Data de Criação", value=processo['data_criacao'], disabled=True, key="upd_data_criacao"
        )
        st.text_input(
            "Data de Término Real", value=processo['data_termino_real'] or "", disabled=True, key="upd_dt_real"
        )
        st.text_input(
            "Tempo Total", value=str(processo['tempo_total']), disabled=True, key="upd_tempo_total"
        )
        st.text_input(
            "Status", value=processo['status'], disabled=True, key="upd_status"
        )

        st.subheader("Etapas do Processo")
        novos_dados_etapas = []
        for etapa in etapas:
            st.markdown(f"**Etapa {etapa['id']}**")
            novo_nome_etapa = st.text_input(
                f"Nome da Etapa {etapa['id']}", value=etapa['nome_etapa'], key=f"upd_nome_etapa_{etapa['id']}"
            )
            novo_resp_etapa = st.text_input(
                f"Responsável da Etapa {etapa['id']}", value=etapa['responsavel_etapa'], key=f"upd_resp_etapa_{etapa['id']}"
            )
            novos_dados_etapas.append((etapa['id'], novo_nome_etapa, novo_resp_etapa))

        # Botão de confirmação
        if st.button("Atualizar Processo", key="btn_atualizar_processo"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE processos SET nome_processo=?, responsavel_geral=?, data_termino_ideal=? WHERE id=?",
                (novo_nome, novo_resp_geral, novo_data_term_ideal, processo_id)
            )
            for eid, nome_et, resp_et in novos_dados_etapas:
                cursor.execute(
                    "UPDATE etapas SET nome_etapa=?, responsavel_etapa=? WHERE id=?",
                    (nome_et, resp_et, eid)
                )
            conn.commit()
            conn.close()
            st.success("Processo e etapas atualizados com sucesso!")
