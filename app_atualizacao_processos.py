import streamlit as st
from db_connect import get_connection
import datetime

# Helper para combinar data e hora no formato brasileiro sem segundos
def combine_date_time(date_obj, time_obj):
    return f"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}"

# Função principal para atualizar processos
def atualizar_processo():
    st.title("Atualizar Processo")

    # 3.0 – filtro lateral para nome do processo
    filtro = st.sidebar.text_input("Filtrar por nome do processo", key="upd_filtro")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_processo FROM processos WHERE nome_processo LIKE ?", (f"%{filtro}%",))
    processos = cursor.fetchall()
    conn.close()

    if not processos:
        st.info("Nenhum processo encontrado para atualizar.")
        return

    # Dropdown dinâmico com processos filtrados
    nomes = [p['nome_processo'] for p in processos]
    selected_name = st.selectbox("Selecione o processo", nomes, key="upd_select")
    selected_id = next(p['id'] for p in processos if p['nome_processo'] == selected_name)

    # Carrega processo e etapas
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM processos WHERE id = ?", (selected_id,))
    proc = cursor.fetchone()
    cursor.execute("SELECT * FROM etapas WHERE processo_id = ? ORDER BY id", (selected_id,))
    etapas = cursor.fetchall()
    conn.close()

    # 3.2 – Títulos atualizados
    st.subheader("Atualize os dados do processo")
    # 3.1 – preenche valor atual para não zerar campos não modificados
    nome = st.text_input("Nome do Processo", value=proc["nome_processo"], key="upd_name")
    resp_geral = st.text_input("Responsável Geral", value=proc["responsavel_geral"], key="upd_resp")

    # Data/Hora de Término Ideal com seletores
    try:
        dt_ideal = datetime.datetime.strptime(proc["data_termino_ideal"], "%d/%m/%Y %H:%M")
    except:
        dt_ideal = datetime.datetime.now()
    novo_date_ideal = st.date_input("Data de Término Ideal", value=dt_ideal.date(), key="upd_date_ideal")
    novo_time_ideal = st.time_input("Hora de Término Ideal", value=dt_ideal.time(), key="upd_time_ideal")
    data_termino_ideal = combine_date_time(novo_date_ideal, novo_time_ideal)

    st.subheader("Dados de Criação e tempo total")
    st.text_input("Data de Criação", value=proc["data_criacao"], disabled=True)
    st.text_input("Tempo Total", value=str(proc["tempo_total"]), disabled=True)

    st.subheader("Atualize o Andamento das Etapas")
    # 3.3 – adiciona/remover etapas
    if st.button("Adicionar Etapa", key="add_step"):
        etapas = list(etapas) + [{"id": 0, "nome_etapa": "", "responsavel_etapa": ""}]
    if st.button("Remover Etapa", key="remove_step") and len(etapas) > 1:
        etapas = etapas[:-1]

    updated_etapas = []
    for idx, etapa in enumerate(etapas):
        # 3.5 – sem numeração nos labels
        nome_et = st.text_input("Nome da Etapa", value=etapa.get("nome_etapa", ""), key=f"upd_et_name_{idx}")
        resp_et = st.text_input("Responsável da Etapa", value=etapa.get("responsavel_etapa", ""), key=f"upd_et_resp_{idx}")
        # 3.4 – seletor de data/hora para Término Real
        if etapa.get("data_termino_real"):
            try:
                dt_real = datetime.datetime.strptime(etapa["data_termino_real"], "%d/%m/%Y %H:%M")
            except:
                dt_real = datetime.datetime.now()
        else:
            dt_real = datetime.datetime.now()
        date_real = st.date_input("Data de Término Real", value=dt_real.date(), key=f"upd_et_date_{idx}")
        time_real = st.time_input("Hora de Término Real", value=dt_real.time(), key=f"upd_et_time_{idx}")
        data_termino_real = combine_date_time(date_real, time_real)
        updated_etapas.append((etapa.get("id", 0), nome_et, resp_et, data_termino_real))

    if st.button("Salvar Alterações", key="upd_save"):
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute(
            "UPDATE processos SET nome_processo = ?, responsavel_geral = ?, data_termino_ideal = ? WHERE id = ?",
            (nome, resp_geral, data_termino_ideal, selected_id)
        )
        for eid, ne, re, dtr in updated_etapas:
            if eid and eid != 0:
                cursor.execute(
                    "UPDATE etapas SET nome_etapa = ?, responsavel_etapa = ?, data_termino_real = ? WHERE id = ?",
                    (ne, re, dtr, eid)
                )
            else:
                cursor.execute(
                    "INSERT INTO etapas (processo_id, nome_etapa, responsavel_etapa, tempo_gasto, data_termino_real) VALUES (?, ?, ?, 0, ?)",
                    (selected_id, ne, re, dtr)
                )
        conn.commit(); conn.close()
        st.success("Processo e etapas atualizados com sucesso!")
