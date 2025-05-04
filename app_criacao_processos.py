import streamlit as st
from db_connect import get_connection
from datetime import datetime

def combine_date_time(date, time):
    return datetime.combine(date, time).strftime("%d/%m/%Y %H:%M")

def get_users():
    """Retorna lista de usuários cadastrados"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, nome_amigavel FROM users ORDER BY nome_amigavel")
    users = cursor.fetchall()
    conn.close()
    return [(user['username'], user['nome_amigavel']) for user in users]

def check_create_permission(user):
    """Verifica se o usuário tem permissão para criar processos"""
    nivel = user.get('nivel', 0)
    return nivel in [1, 3, 5, 7, 9, 10]  # Níveis que podem criar processos

def criar_processo():
    # Verifica se o usuário está logado
    if 'user' not in st.session_state:
        st.error("Você precisa estar logado para acessar esta página.")
        return

    user = st.session_state.user

    # Verifica permissão de criação
    if not check_create_permission(user):
        st.error("Você não tem permissão para criar processos.")
        return

    st.title("Criar Novo Processo")
    
    # Busca lista de usuários
    users = get_users()
    user_options = [f"{username} ({nome_amigavel})" for username, nome_amigavel in users]
    
    col_main, col_etapas = st.columns([1, 1])
    with col_main:
        nome_processo = st.text_input("Nome do Processo", key="cp_nome_processo")
        responsavel_geral = st.selectbox("Responsável Geral", options=user_options, key="cp_responsavel_geral")
        etapas_quantidade = st.number_input("Quantidade de Etapas", min_value=1, step=1, value=1, key="cp_qtd_etapas")
        dt_ideal_date = st.date_input("Data de Término Ideal", key="cp_data_termino_ideal_date")
        dt_ideal_time = st.time_input("Hora de Término Ideal", key="cp_data_termino_ideal_time")
        data_termino_ideal = combine_date_time(dt_ideal_date, dt_ideal_time)
    
    with col_etapas:
        st.subheader("Configurar Etapas")
        etapa_nome_list = []
        etapa_resp_list = []
        for i in range(1, int(etapas_quantidade)+1):
            cols = st.columns(2)
            with cols[0]:
                nome_etapa = st.text_input(f"Nome da Etapa {i}", key=f"cp_nome_etapa_{i}")
            with cols[1]:
                responsavel_etapa = st.selectbox(f"Responsável da Etapa {i}", options=user_options, key=f"cp_resp_etapa_{i}")
            etapa_nome_list.append(nome_etapa)
            etapa_resp_list.append(responsavel_etapa)

    if st.button("Criar Processo", key="cp_criar"):
        if not nome_processo:
            st.error("Nome do processo é obrigatório!")
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insere o processo
        cursor.execute("""
            INSERT INTO processos 
            (nome_processo, responsavel_geral, data_termino_ideal, data_criacao, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            nome_processo,
            responsavel_geral.split(" (")[0],  # Pega apenas o username
            data_termino_ideal,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Em andamento"
        ))
        
        processo_id = cursor.lastrowid
        
        # Insere as etapas
        for nome, resp in zip(etapa_nome_list, etapa_resp_list):
            if nome:  # Só insere se tiver nome
                cursor.execute("""
                    INSERT INTO etapas 
                    (processo_id, nome_etapa, responsavel_etapa)
                    VALUES (?, ?, ?)
                """, (
                    processo_id,
                    nome,
                    resp.split(" (")[0]  # Pega apenas o username
                ))
        
        conn.commit()
        conn.close()
        
        st.success("Processo criado com sucesso!")
        st.session_state.pagina = "visualizar"
        st.rerun()
