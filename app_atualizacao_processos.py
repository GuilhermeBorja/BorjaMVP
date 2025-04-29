import streamlit as st
from db_connect import get_connection
import datetime


def combine_date_time(date_obj, time_obj):
    return f"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}"


def atualizar_processo():
    st.header("Atualizar Processo")
    filtro = st.sidebar.text_input("Filtrar processos")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT id, nome_processo FROM processos WHERE nome_processo LIKE ?", (f"%{filtro}%",))
    lista = cur.fetchall(); conn.close()
    if not lista:
        st.info("Nenhum processo encontrado.")
        return
    opcoes = [f"{p['id']:02d} - {p['nome_processo']}" for p in lista]
    escolha = st.selectbox("Selecione", opcoes)
    pid = int(escolha.split(' - ')[0])

    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM processos WHERE id=?", (pid,)); proc = cur.fetchone()
    cur.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (pid,)); ets = cur.fetchall()
    conn.close()

    st.subheader("Atualize os dados do processo")
    nome = st.text_input("Nome do Processo", value=proc['nome_processo'])
    resp = st.text_input("Responsável Geral", value=proc['responsavel_geral'])
    try:
        di = datetime.datetime.strptime(proc['data_termino_ideal'], "%d/%m/%Y %H:%M")
    except:
        di = datetime.datetime.now()
    new_di = st.date_input("Data de Término Ideal", value=di.date())
    new_tm = st.time_input("Hora de Término Ideal", value=di.time())
    termo_ideal = combine_date_time(new_di, new_tm)

    st.subheader("Dados de Criação e Tempo Total")
    st.text_input("Data de Criação", value=proc['data_criacao'], disabled=True)
    st.text_input("Tempo Total", value=proc['tempo_total'], disabled=True)

    st.subheader("Atualize o Andamento das Etapas")
    if st.button("Adicionar Etapa"): ets.append({'id':0,'nome_etapa':'','responsavel_etapa':'','data_termino_real':''})
    if st.button("Remover Etapa") and len(ets)>1: ets.pop()

    updates = []
    for idx, et in enumerate(ets):
        ne = st.text_input("Nome da Etapa", value=et['nome_etapa'], key=f"ne{idx}")
        re_ = st.text_input("Responsável da Etapa", value=et['responsavel_etapa'], key=f"re{idx}")
        try:
            dr = datetime.datetime.strptime(et['data_termino_real'], "%d/%m/%Y %H:%M")
        except:
            dr = datetime.datetime.now()
        dr_date = st.date_input("Data de Término Real", value=dr.date(), key=f"drd{idx}")
        dr_time = st.time_input("Hora de Término Real", value=dr.time(), key=f"drt{idx}")
        dt_real = combine_date_time(dr_date, dr_time)
        updates.append((et['id'], ne, re_, dt_real))

    if st.button("Salvar Alterações"):
        conn = get_connection(); cur = conn.cursor()
        cur.execute("UPDATE processos SET nome_processo=?, responsavel_geral=?, data_termino_ideal=? WHERE id=?",
                    (nome, resp, termo_ideal, pid))
        for eid, ne, re_, dr in updates:
            if eid:
                cur.execute("UPDATE etapas SET nome_etapa=?, responsavel_etapa=?, data_termino_real=? WHERE id=?",
                            (ne, re_, dr, eid))
            else:
                cur.execute("INSERT INTO etapas (processo_id,nome_etapa,responsavel_etapa,data_termino_real,tempo_gasto) VALUES (?,?,?,?,?)",
                            (pid, ne, re_, dr, "0d 0h 0m 0s"))
        conn.commit(); conn.close()
        st.success("Processo e etapas atualizados com sucesso!")
