import streamlit as st
from db_connect import get_connection
import datetime

def combine_dt(date_obj, time_obj):
    return f\"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}\"

def atualizar_processo():
    st.title("Atualizar Processo")
    # 3.0 – filtro lateral
    filtro = st.sidebar.text_input("Filtro Nome", key="upd_filtro")
    conn = get_connection(); c=conn.cursor()
    c.execute("SELECT nome_processo FROM processos WHERE nome_processo LIKE ?", (f"%{filtro}%",))
    nomes = [r["nome_processo"] for r in c.fetchall()]; conn.close()
    sel = st.selectbox("Processo", nomes, key="upd_sel")

    if not sel:
        st.info("Escolha processo")
        return
    pid = get_connection().cursor().execute(
        "SELECT id FROM processos WHERE nome_processo=?", (sel,)).fetchone()["id"]

    # Carrega
    conn=get_connection(); c=conn.cursor()
    c.execute("SELECT * FROM processos WHERE id=?", (pid,)); proc=c.fetchone()
    c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (pid,)); ets=c.fetchall()
    conn.close()

    # 3.2 – títulos trocados
    st.subheader("Atualize os dados do processo")
    # usa value=prefill para não zerar (3.1)
    nome = st.text_input("Nome do Processo", value=proc["nome_processo"], key="u_nome")
    resp = st.text_input("Responsável Geral", value=proc["responsavel_geral"], key="u_resp")
    # data término ideal
    dt_ideal = datetime.datetime.strptime(proc["data_termino_ideal"], "%d/%m/%Y %H:%M")
    di = st.date_input("Data de Término Ideal", value=dt_ideal.date(), key="u_di")
    ti = st.time_input("Hora de Término Ideal", value=dt_ideal.time(), key="u_hi")
    novo_ideal = combine_dt(di, ti)

    st.subheader("Dados de Criação e tempo total")
    st.text_input("Data de Criação", value=proc["data_criacao"], disabled=True)
    st.text_input("Tempo Total", value=str(proc["tempo_total"]), disabled=True)

    st.subheader("Atualize o Andamento das Etapas")
    # 3.3 – botões adicionar/remover
    if st.button("Adicionar Etapa", key="add_et"):
        ets.append({"id":0,"nome_etapa":"","responsavel_etapa":"","data_termino_real":""})
    if st.button("Remover Etapa", key="rm_et") and len(ets)>1:
        ets.pop()

    novos = []
    for et in ets:
        # 3.5 – sem numeração
        nome_et = st.text_input("Nome da Etapa", value=et["nome_etapa"], key=f"u_ne_{et['id']}")
        resp_et = st.text_input("Responsável da Etapa", value=et["responsavel_etapa"], key=f"u_re_{et['id']}")
        # 3.4 – date & time picker
        if et["data_termino_real"]:
            dtre = datetime.datetime.strptime(et["data_termino_real"], "%d/%m/%Y %H:%M")
        else:
            dtre = datetime.datetime.now()
        dre_date = st.date_input("Término Real", value=dtre.date(), key=f"u_dre_d_{et['id']}")
        dre_time = st.time_input("Hora Término", value=dtre.time(), key=f"u_dre_t_{et['id']}")
        novo_dtre = combine_dt(dre_date, dre_time)
        novos.append((et["id"], nome_et or et["nome_etapa"], resp_et or et["responsavel_etapa"], novo_dtre))

    if st.button("Salvar Alterações", key="u_salvar"):
        conn=get_connection(); c=conn.cursor()
        c.execute("UPDATE processos SET nome_processo=?, responsavel_geral=?, data_termino_ideal=? WHERE id=?",
                  (nome, resp, novo_ideal, pid))
        for eid, ne, re, tr in novos:
            if eid:
                c.execute("UPDATE etapas SET nome_etapa=?, responsavel_etapa=?, data_termino_real=? WHERE id=?",
                          (ne, re, tr, eid))
            else:
                c.execute("INSERT INTO etapas (processo_id,nome_etapa,responsavel_etapa,data_termino_real,tempo_gasto) VALUES (?,?,?,?,0)",
                          (pid, ne, re, tr))
        conn.commit(); conn.close()
        st.success("Atualizado com sucesso!")
