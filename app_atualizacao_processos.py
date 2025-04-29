import streamlit as st
from db_connect import get_connection
import datetime

def combine_date_time(d, t):
    return f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}"

def atualizar_processo():
    st.header("Atualizar Processo")

    # 3.0 filtro na sidebar
    filtro = st.sidebar.text_input("Filtrar por nome", key="up_filtro")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT id,nome_processo FROM processos WHERE nome_processo LIKE ?", (f"%{filtro}%",))
    lista = cur.fetchall(); conn.close()
    if not lista:
        st.info("Nenhum processo encontrado."); return

    # dropdown dinâmico
    op = [f"{p['id']:02d} - {p['nome_processo']}" for p in lista]
    sel = st.selectbox("Selecione o processo", op, key="up_sel")
    pid = int(sel.split(" - ")[0])

    # busca dados
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM processos WHERE id=?", (pid,)); proc = cur.fetchone()
    cur.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (pid,)); ets = cur.fetchall()
    conn.close()

    # 3.2
    st.subheader("Atualize os dados do processo")
    nome = st.text_input("Nome do Processo", value=proc["nome_processo"], key="up_nome")
    resp = st.text_input("Responsável Geral", value=proc["responsavel_geral"], key="up_resp")

    # termo ideal
    try:
        di0 = datetime.datetime.strptime(proc["data_termino_ideal"],"%d/%m/%Y %H:%M")
    except:
        di0 = datetime.datetime.now()
    dnew = st.date_input("Data de Término Ideal", value=di0.date(), key="up_date")
    tnew = st.time_input("Hora de Término Ideal", value=di0.time(), key="up_time")
    termo_ideal = combine_date_time(dnew, tnew)

    # 3.2
    st.subheader("Dados de Criação e tempo total")
    st.text_input("Data de Criação", proc["data_criacao"], disabled=True)
    st.text_input("Tempo Total", proc["tempo_total"], disabled=True)

    # controla quantidade de etapas
    cnt_key = f"up_cnt_{pid}"
    if cnt_key not in st.session_state:
        st.session_state[cnt_key] = len(ets)
    if st.button("Adicionar Etapa", key="up_add"):
        st.session_state[cnt_key] += 1
    if st.button("Remover Etapa", key="up_rem") and st.session_state[cnt_key]>1:
        st.session_state[cnt_key] -= 1

    st.subheader("Atualize o Andamento das Etapas")
    updates=[]
    for i in range(st.session_state[cnt_key]):
        # usa dados existentes quando disponíveis
        e = ets[i] if i<len(ets) else {"id":0,"nome_etapa":"","responsavel_etapa":"","data_termino_real":""}
        ne = st.text_input("Nome da Etapa", value=e["nome_etapa"], key=f"up_ne_{i}")
        re_ = st.text_input("Responsável da Etapa", value=e["responsavel_etapa"], key=f"up_re_{i}")
        # 3.4
        try:
            dr0 = datetime.datetime.strptime(e["data_termino_real"],"%d/%m/%Y %H:%M")
        except:
            dr0 = datetime.datetime.now()
        drd = st.date_input("Data de Término Real", value=dr0.date(), key=f"up_drd_{i}")
        drt = st.time_input("Hora de Término Real", value=dr0.time(), key=f"up_drt_{i}")
        dr = combine_date_time(drd, drt)
        updates.append((e["id"], ne, re_, dr))

    # salvar
    if st.button("Salvar Alterações", key="up_save"):
        conn = get_connection(); cur = conn.cursor()
        cur.execute(
            "UPDATE processos SET nome_processo=?,responsavel_geral=?,data_termino_ideal=? WHERE id=?",
            (nome, resp, termo_ideal, pid)
        )
        # 3.1 só altera o que mudou (fallback)
        for eid, ne, re_, dr in updates:
            if eid:
                cur.execute(
                  "UPDATE etapas SET nome_etapa=?,responsavel_etapa=?,data_termino_real=? WHERE id=?",
                  (ne or e["nome_etapa"], re_ or e["responsavel_etapa"], dr, eid)
                )
            else:
                cur.execute(
                  "INSERT INTO etapas (processo_id,nome_etapa,responsavel_etapa,data_termino_real,tempo_gasto) VALUES (?,?,?,?,?)",
                  (pid, ne, re_, dr, "0d 0h 0m 0s")
                )
        conn.commit(); conn.close()
        st.success("Processo e etapas atualizados com sucesso!")
