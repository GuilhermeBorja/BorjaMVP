import streamlit as st
from db_connect import get_connection
import datetime


def combine_date_time(date_obj, time_obj):
    return f"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}"


def atualizar_processo():
    st.header("Atualizar Processo")
    filtro = st.sidebar.text_input("Filtrar por nome do processo", key="upd_filtro")
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id, nome_processo FROM processos WHERE nome_processo LIKE ?", (f"%{filtro}%",))
    processos = cursor.fetchall()
    conn.close()

    if not processos:
        st.info("Nenhum processo encontrado para atualizar.")
        return

    nomes = [p['nome_processo'] for p in processos]
    selected = st.selectbox("Selecione o processo", nomes, key="upd_select")
    pid = next(p['id'] for p in processos if p['nome_processo'] == selected)

    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM processos WHERE id=?", (pid,))
    proc = cursor.fetchone()
    cursor.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (pid,))
    etapas = cursor.fetchall()
    conn.close()

    st.subheader("Atualize os dados do processo")
    nome = st.text_input("Nome do Processo", value=proc['nome_processo'], key="upd_nome")
    resp_geral = st.text_input("Responsável Geral", value=proc['responsavel_geral'], key="upd_resp")

    try:
        dt_ideal = datetime.datetime.strptime(proc['data_termino_ideal'], "%d/%m/%Y %H:%M")
    except:
        dt_ideal = datetime.datetime.now()
    new_date = st.date_input("Data de Término Ideal", value=dt_ideal.date(), key="upd_date")
    new_time = st.time_input("Hora de Término Ideal", value=dt_ideal.time(), key="upd_time")
    termo_ideal = combine_date_time(new_date, new_time)

    st.subheader("Dados de Criação e tempo total")
    st.text_input("Data de Criação", value=proc['data_criacao'], disabled=True)
    st.text_input("Tempo Total", value=proc['tempo_total'], disabled=True)

    st.subheader("Atualize o Andamento das Etapas")
    if st.button("Adicionar Etapa", key="add_etapa"): etapas = etapas + [ {'id':0,'nome_etapa':'','responsavel_etapa':'','data_termino_real':''} ]
    if st.button("Remover Etapa", key="remove_etapa") and len(etapas)>1: etapas = etapas[:-1]

    updated = []
    for idx, et in enumerate(etapas):
        name_et = st.text_input("Nome da Etapa", value=et['nome_etapa'], key=f"upd_et_name_{idx}")
        rep_et  = st.text_input("Responsável da Etapa", value=et['responsavel_etapa'], key=f"upd_et_rep_{idx}")
        try:
            dr = datetime.datetime.strptime(et['data_termino_real'], "%d/%m/%Y %H:%M")
        except:
            dr = datetime.datetime.now()
        d_real = st.date_input("Data de Término Real", value=dr.date(), key=f"upd_et_date_{idx}")
        t_real = st.time_input("Hora de Término Real", value=dr.time(), key=f"upd_et_time_{idx}")
        data_real = combine_date_time(d_real, t_real)
        updated.append((et['id'], name_et, rep_et, data_real))

    if st.button("Salvar Alterações", key="upd_salvar"):
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE processos SET nome_processo=?, responsavel_geral=?, data_termino_ideal=? WHERE id=?",
                       (nome, resp_geral, termo_ideal, pid))
        for eid, ne, re, dr in updated:
            if eid:
                cursor.execute("UPDATE etapas SET nome_etapa=?, responsavel_etapa=?, data_termino_real=? WHERE id=?",
                               (ne, re, dr, eid))
            else:
                cursor.execute("INSERT INTO etapas (processo_id,nome_etapa,responsavel_etapa,data_termino_real,tempo_gasto) VALUES (?,?,?,?,?)",
                               (pid, ne, re, dr, "0d 0h 0m 0s"))
        conn.commit(); conn.close()
        st.success("Processo e etapas atualizados com sucesso!")
