import streamlit as st
from db_connect import get_connection
import datetime

def combine_date_time(d, t):
    return f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}"

def atualizar_processo():
    # Check if we have a pre-selected process
    if 'processo_para_editar' in st.session_state:
        pid = st.session_state.processo_para_editar
        # Clear the pre-selected process
        del st.session_state.processo_para_editar
    else:
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

    st.subheader("Atualize o Andamento das Etapas")
    updates=[]
    
    # Initialize the number of stages in session state if not exists
    session_key = f'up_qtd_etapas_{pid}'
    if session_key not in st.session_state:
        st.session_state[session_key] = len(ets)
    
    # Get the current number of stages
    qtd_etapas = st.session_state[session_key]
    
    for i in range(qtd_etapas):
        # usa dados existentes quando disponíveis
        e = ets[i] if i<len(ets) else {"id":0,"nome_etapa":"","responsavel_etapa":"","data_termino_real":""}
        
        # Create columns for stage information
        if 'etapa_concluida' not in st.session_state:
            st.session_state.etapa_concluida = {}
        
        # Initialize the checkbox state for this stage if not exists
        if f"etapa_{i}" not in st.session_state.etapa_concluida:
            st.session_state.etapa_concluida[f"etapa_{i}"] = bool(e["data_termino_real"])
        
        # Create a single row with all fields
        cols = st.columns([2, 2, 1, 1, 1])
        
        with cols[0]:
            ne = st.text_input("Nome da Etapa", value=e["nome_etapa"], key=f"up_ne_{i}")
        with cols[1]:
            re_ = st.text_input("Responsável da Etapa", value=e["responsavel_etapa"], key=f"up_re_{i}")
        with cols[2]:
            etapa_concluida = st.checkbox("Concluída?", value=st.session_state.etapa_concluida[f"etapa_{i}"], key=f"up_concluida_{i}")
            st.session_state.etapa_concluida[f"etapa_{i}"] = etapa_concluida
        
        if etapa_concluida:
            with cols[3]:
                try:
                    dr0 = datetime.datetime.strptime(e["data_termino_real"],"%d/%m/%Y %H:%M")
                except:
                    dr0 = datetime.datetime.now()
                drd = st.date_input("Data", value=dr0.date(), key=f"up_drd_{i}")
            with cols[4]:
                drt = st.time_input("Hora", value=dr0.time(), key=f"up_drt_{i}")
            dr = combine_date_time(drd, drt)
        else:
            dr = ""  # Empty string for not completed stages
        
        updates.append((e["id"], ne, re_, dr))
    
    # Add number input for stage quantity at the end of the stages section
    nova_qtd = st.number_input("Quantidade de Etapas", min_value=1, step=1, value=qtd_etapas, key=f"up_qtd_etapas_input_{pid}")
    if nova_qtd != qtd_etapas:
        st.session_state[session_key] = nova_qtd
        st.rerun()

    st.header("Atualizar Processo")
    # 3.2
    st.subheader("Atualize os dados do processo")
    
    # Create columns for process data
    proc_cols = st.columns([2, 2, 1, 1])
    with proc_cols[0]:
        nome = st.text_input("Nome do Processo", value=proc["nome_processo"], key="up_nome")
    with proc_cols[1]:
        resp = st.text_input("Responsável Geral", value=proc["responsavel_geral"], key="up_resp")
    with proc_cols[2]:
        try:
            di0 = datetime.datetime.strptime(proc["data_termino_ideal"],"%d/%m/%Y %H:%M")
        except:
            di0 = datetime.datetime.now()
        dnew = st.date_input("Data de Término Ideal", value=di0.date(), key="up_date")
    with proc_cols[3]:
        tnew = st.time_input("Hora de Término Ideal", value=di0.time(), key="up_time")
    termo_ideal = combine_date_time(dnew, tnew)

    # 3.2
    st.subheader("Dados de Criação e tempo total")
    # Create columns for creation data
    create_cols = st.columns(2)
    with create_cols[0]:
        st.text_input("Data de Criação", proc["data_criacao"], disabled=True)
    with create_cols[1]:
        st.text_input("Tempo Total", proc["tempo_total"], disabled=True)

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
        # Return to visualization page after saving
        st.session_state.pagina = "visualizar"
        st.rerun()
