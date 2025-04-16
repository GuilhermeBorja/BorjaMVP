import streamlit as st
from db_connect import get_connection
import datetime

def atualizar_processo():
    st.header("Atualizar Processo")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_processo FROM processos")
    processos = cursor.fetchall()
    conn.close()
    
    if processos:
        processos_dict = {p["nome_processo"]: p["id"] for p in processos}
        processo_selecionado = st.selectbox("Selecione o Processo (por Nome)", list(processos_dict.keys()), key="upd_select_processo")
        
        if processo_selecionado:
            processo_id = processos_dict[processo_selecionado]
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM processos WHERE id=?", (processo_id,))
            processo = cursor.fetchone()
            cursor.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (processo_id,))
            etapas = cursor.fetchall()
            conn.close()
            
            st.subheader("Atualize os Dados Editáveis")
            novo_nome = st.text_input("Nome do Processo", value=processo["nome_processo"], key="upd_nome_processo")
            novo_resp_geral = st.text_input("Responsável Geral", value=processo["responsavel_geral"], key="upd_resp_geral")
            # Atualiza data de término ideal com seletores de data e hora
            dt_term_ideal = None
            if processo["data_termino_ideal"]:
                try:
                    dt_term_ideal = datetime.datetime.strptime(processo["data_termino_ideal"], "%d/%m/%Y %H:%M:%S")
                except:
                    dt_term_ideal = datetime.datetime.now()
            else:
                dt_term_ideal = datetime.datetime.now()
            novo_dt_ideal_date = st.date_input("Data de Término Ideal", value=dt_term_ideal.date(), key="upd_dt_ideal_date")
            novo_dt_ideal_time = st.time_input("Hora de Término Ideal", value=dt_term_ideal.time(), key="upd_dt_ideal_time")
            novo_data_term_ideal = novo_dt_ideal_date.strftime("%d/%m/%Y") + " " + novo_dt_ideal_time.strftime("%H:%M:%S")
            # Exibe Data de Término Real (não editável)
            st.text_input("Data de Término Real", value=processo["data_termino_real"] if processo["data_termino_real"] else "", disabled=True, key="upd_dt_real")
            
            st.subheader("Dados Não Editáveis")
            st.text_input("Data de Criação", value=processo["data_criacao"], disabled=True, key="upd_data_criacao")
            st.text_input("Tempo Total", value=str(processo["tempo_total"]), disabled=True, key="upd_tempo_total")
            
            st.subheader("Atualize as Etapas (Editáveis)")
            novos_dados_etapas = []
            for etapa in etapas:
                col1, col2, col3 = st.columns(3)
                with col1:
                    novo_nome_etapa = st.text_input(f"Nome da Etapa {etapa['id']}", value=etapa["nome_etapa"], key=f"upd_nome_etapa_{etapa['id']}")
                with col2:
                    novo_resp_etapa = st.text_input(f"Responsável da Etapa {etapa['id']}", value=etapa["responsavel_etapa"], key=f"upd_resp_etapa_{etapa['id']}")
                with col3:
                    novo_dt_term_etapa = st.text_input(f"Término Real Etapa {etapa['id']}", value=etapa["data_termino_real"] if etapa["data_termino_real"] else "", key=f"upd_dt_term_etapa_{etapa['id']}")
                novos_dados_etapas.append((etapa["id"], novo_nome_etapa, novo_resp_etapa, novo_dt_term_etapa))
            
            if st.button("Atualizar Processo", key="btn_atualizar_processo"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE processos SET nome_processo=?, responsavel_geral=?, data_termino_ideal=? WHERE id=?",
                    (novo_nome, novo_resp_geral, novo_data_term_ideal, processo_id)
                )
                for etapa_id, nome_at, resp_at, dt_term in novos_dados_etapas:
                    cursor.execute(
                        "UPDATE etapas SET nome_etapa=?, responsavel_etapa=?, data_termino_real=? WHERE id=?",
                        (nome_at, resp_at, dt_term, etapa_id)
                    )
                conn.commit()
                conn.close()
                st.success("Processo e etapas atualizados com sucesso!")
    else:
        st.info("Nenhum processo cadastrado para atualizar.")
