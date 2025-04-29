import streamlit as st
from db_connect import get_connection
import datetime

# Helper para combinar data e hora no formato brasileiro sem segundos
def combine_date_time(date_obj, time_obj):
    return f"{date_obj.strftime('%d/%m/%Y')} {time_obj.strftime('%H:%M')}"

# Função para atualizar processos
def atualizar_processo():
    st.title("Atualizar Processo")

    # Filtro de nome de processo na sidebar
    filtro = st.sidebar.text_input("Filtrar por nome do processo", key="upd_filtro")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome_processo FROM processos WHERE nome_processo LIKE ?",
        (f"%{filtro}%",)
    )
    processos = cursor.fetchall()
    conn.close()

    if not processos:
        st.info("Nenhum processo encontrado para atualizar.")
        return

    # Dropdown com processos filtrados
    nomes = [p['nome_processo'] for p in processos]
    selected_name = st.selectbox("Selecione o processo", nomes, key="upd_select")
    selected = next(p for p in processos if p['nome_processo'] == selected_name)
    proc_id = selected['id']

    # Carrega dados do processo e suas etapas
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processos WHERE id = ?", (proc_id,))
    proc = cursor.fetchone()
    cursor.execute(
        "SELECT * FROM etapas WHERE processo_id = ? ORDER BY id",
        (proc_id,)
    )
    etapas = cursor.fetchall()
    conn.close()

    # Títulos solicitados
    st.subheader("Atualize os dados do processo")
    # Campos editáveis pré-preenchidos para não zerar
    nome = st.text_input(
        "Nome do Processo", value=proc['nome_processo'], key="upd_nome"
    )
    resp_geral = st.text_input(
        "Responsável Geral", value=proc['responsavel_geral'], key="upd_resp_geral"
    )

    # Seletor de data/hora para Data de Término Ideal
    try:
        dt_ideal = datetime.datetime.strptime(proc['data_termino_ideal'], "%d/%m/%Y %H:%M")
    except:
        dt_ideal = datetime.datetime.now()
    novo_date_ideal = st.date_input(
        "Data de Término Ideal", value=dt_ideal.date(), key="upd_date_ideal"
    )
    novo_time_ideal = st.time_input(
        "Hora de Término Ideal", value=dt_ideal.time(), key="upd_time_ideal"
    )
    data_termino_ideal = combine_date_time(novo_date_ideal, novo_time_ideal)

    st.subheader("Dados de Criação e tempo total")
    st.text_input(
        "Data de Criação", value=proc['data_criacao'], disabled=True
    )
    st.text_input(
        "Tempo Total", value=str(proc['tempo_total']), disabled=True
    )

    st.subheader("Atualize o Andamento das Etapas")
    # Botões para adicionar/remover etapas
    if st.button("Adicionar Etapa", key="add_etapa"):
        etapas = list(etapas) + [{ 'id': 0, 'nome_etapa': '', 'responsavel_etapa': '', 'data_termino_real': '' }]
    if st.button("Remover Etapa", key="remove_etapa") and len(etapas) > 1:
        etapas = etapas[:-1]

    novos = []
    for idx, et in enumerate(etapas):
        nome_et = st.text_input(
            "Nome da Etapa", value=et.get('nome_etapa', ''), key=f"upd_et_nome_{idx}"
        )
        resp_et = st.text_input(
            "Responsável da Etapa", value=et.get('responsavel_etapa', ''), key=f"upd_et_resp_{idx}"
        )
        try:
            dt_real = datetime.datetime.strptime(
                et.get('data_termino_real', ''), "%d/%m/%Y %H:%M"
            )
        except:
            dt_real = datetime.datetime.now()
        date_real = st.date_input(
            "Data de Término Real", value=dt_real.date(), key=f"upd_et_date_{idx}"
        )
        time_real = st.time_input(
            "Hora de Término Real", value=dt_real.time(), key=f"upd_et_time_{idx}"
        )
        data_real = combine_date_time(date_real, time_real)
        novos.append((et.get('id', 0), nome_et, resp_et, data_real))

    if st.button("Salvar Alterações", key="upd_salvar"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE processos SET nome_processo=?, responsavel_geral=?, data_termino_ideal=? WHERE id=?",
            (nome, resp_geral, data_termino_ideal, proc_id)
        )
        for eid, ne, re, dr in novos:
            if eid and eid != 0:
                cursor.execute(
                    "UPDATE etapas SET nome_etapa=?, responsavel_etapa=?, data_termino_real=? WHERE id=?",
                    (ne, re, dr, eid)
                )
            else:
                cursor.execute(
                    "INSERT INTO etapas (processo_id,nome_etapa,responsavel_etapa,data_termino_real,tempo_gasto) VALUES (?,?,?,?,0)",
                    (proc_id, ne, re, dr)
                )
        conn.commit()
        conn.close()
        st.success("Processo e etapas atualizados com sucesso!")
