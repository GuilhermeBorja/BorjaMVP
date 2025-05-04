import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos

def get_local_now():
    return datetime.datetime.now() + datetime.timedelta(hours=st.session_state.get('tz_offset', 0)/60)

def format_timedelta(delta):
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

def calcular_tempo_total(processo, etapas):
    try:
        dt0 = datetime.datetime.strptime(processo["data_criacao"], "%d/%m/%Y %H:%M")
    except:
        return ""
    if etapas and all(e["data_termino_real"] for e in etapas):
        dt1 = datetime.datetime.strptime(etapas[-1]["data_termino_real"], "%d/%m/%Y %H:%M")
        delta = dt1 - dt0
    else:
        delta = get_local_now() - dt0
    return format_timedelta(delta)

def get_user_access_filter(user):
    """Retorna a condição SQL baseada no nível de acesso do usuário"""
    nivel = user.get('nivel', 0)
    username = user.get('username', '')
    estado = user.get('estado', '')
    empresa = user.get('empresa', '')
    setor = user.get('setor', '')

    if nivel == 10:  # Admin - acesso total
        return "1=1", []
    
    # Busca informações dos responsáveis
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, estado, empresa, setor 
        FROM users 
        WHERE username IN (
            SELECT DISTINCT responsavel_geral FROM processos
            UNION
            SELECT DISTINCT responsavel_etapa FROM etapas
        )
    """)
    responsaveis = {row['username']: row for row in cursor.fetchall()}
    conn.close()

    if nivel == 1:  # Apenas dados criados pelo usuário
        return "responsavel_geral = ?", [username]
    elif nivel == 2:  # Visualizar dados do estado
        return "responsavel_geral IN (SELECT username FROM users WHERE estado = ?)", [estado]
    elif nivel == 3:  # Editar dados do estado
        return "responsavel_geral IN (SELECT username FROM users WHERE estado = ?)", [estado]
    elif nivel == 4:  # Visualizar dados do setor
        return "responsavel_geral IN (SELECT username FROM users WHERE setor = ?)", [setor]
    elif nivel == 5:  # Editar dados do setor
        return "responsavel_geral IN (SELECT username FROM users WHERE setor = ?)", [setor]
    elif nivel == 6:  # Visualizar dados da empresa
        return "responsavel_geral IN (SELECT username FROM users WHERE empresa = ?)", [empresa]
    elif nivel == 7:  # Editar dados da empresa
        return "responsavel_geral IN (SELECT username FROM users WHERE empresa = ?)", [empresa]
    elif nivel == 8:  # Visualizar todos os dados
        return "1=1", []
    elif nivel == 9:  # Editar todos os dados
        return "1=1", []
    else:
        return "1=0", []  # Nenhum acesso

def painel_visual(user):
    st.header("Visualização de Processos")
    filtros = filtros_processos()

    # Obtém a condição de acesso baseada no nível do usuário
    access_condition, access_params = get_user_access_filter(user)
    
    # Monta a query base
    query = "SELECT * FROM processos WHERE " + access_condition
    params = access_params

    # Adiciona filtros do usuário
    if filtros["nome"]:
        query += " AND nome_processo LIKE ?"
        params.append(f"%{filtros['nome']}%")
    
    if filtros["responsavel"] and filtros["responsavel"] != "Todos":
        query += " AND responsavel_geral = ?"
        params.append(filtros["responsavel"])
    
    if filtros["status"] and filtros["status"] != "Todos":
        query += " AND status = ?"
        params.append(filtros["status"])
    
    if filtros["data_inicio"] and filtros["data_fim"]:
        d0 = filtros["data_inicio"].strftime("%d/%m/%Y")
        d1 = (filtros["data_fim"] + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        query += " AND substr(data_criacao,1,10)>=? AND substr(data_criacao,1,10)<=?"
        params += [d0, d1]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    procs = cur.fetchall()
    conn.close()

    def fmt_id(x): return f"{x:02d}"

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Visualização Sintética", "Visualização Analítica"])

    with tab1:
        if procs:
            # Create columns for the table and action buttons
            col1, col2 = st.columns([0.95, 0.05])
            
            with col1:
                df = []
                for p in procs:
                    c = get_connection().cursor()
                    c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p["id"],))
                    ets = c.fetchall()
                    c.connection.close()
                    df.append({
                        "ID": fmt_id(p["id"]),
                        "Nome": p["nome_processo"],
                        "Resp. Geral": p["responsavel_geral"],
                        "Criação": p["data_criacao"],
                        "Término Ideal": p["data_termino_ideal"],
                        "Término Real": p["data_termino_real"] or "",
                        "Tempo Total": calcular_tempo_total(p, ets),
                        "Status": p["status"]
                    })
                table = pd.DataFrame(df)
                st.dataframe(
                    table.style.set_properties(**{"text-align": "center"}),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                st.write("")  # Add some space to align with table
                st.write("")  # Add some space to align with table
                for p in procs:
                    # Create a row with edit and delete buttons
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        # Verifica se o usuário tem permissão para editar
                        can_edit = user['nivel'] in [3, 5, 7, 9, 10] or p['responsavel_geral'] == user['username']
                        if can_edit and st.button("✏️", key=f"edit_{p['id']}", help="Editar processo"):
                            st.session_state.pagina = "atualizar"
                            st.session_state.processo_para_editar = p["id"]
                            st.rerun()
                    with col_del:
                        # Apenas admin pode deletar
                        if user['nivel'] == 10 and st.button("🗑️", key=f"del_{p['id']}", help="Apagar processo"):
                            delete_processo(p["id"])
                            st.rerun()
        else:
            st.info("Nenhum processo encontrado.")

    with tab2:
        for p in procs:
            st.markdown(f"### {p['nome_processo']}")
            c = get_connection().cursor()
            c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p["id"],))
            ets = c.fetchall()
            c.connection.close()
            dt_prev = datetime.datetime.strptime(p["data_criacao"], "%d/%m/%Y %H:%M")
            seq=[]
            for idx, e in enumerate(ets):
                cor="#28a745" if e["data_termino_real"] else "#ffc107"
                if e["data_termino_real"]:
                    dt_now = datetime.datetime.strptime(e["data_termino_real"], "%d/%m/%Y %H:%M")
                else:
                    dt_now = get_local_now()
                tempo = format_timedelta(dt_now - dt_prev)
                dt_prev = dt_now
                seq.append(f"""
                  <div style="display:inline-block;text-align:center;margin:10px;">
                    <div style="width:60px;height:60px;border-radius:50%;background:{cor};
                        display:flex;align-items:center;justify-content:center;">
                      <span style="font-size:10px;word-wrap:break-word;">{e['nome_etapa']}</span>
                    </div>
                    <div style="font-size:10px;text-align:center;">
                      {e['responsavel_etapa']}<br>{tempo}
                    </div>
                  </div>
                """)
                if idx < len(ets)-1:
                    seq.append('<span style="display:inline-flex;align-items:center;font-size:24px;">&#8594;</span>')
            html = "<div style='text-align:center'>" + "".join(seq) + "</div>"
            st.markdown(html, unsafe_allow_html=True)

def delete_processo(pid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM etapas WHERE processo_id=?", (pid,))
    cursor.execute("DELETE FROM processos WHERE id=?", (pid,))
    conn.commit()
    conn.close()
