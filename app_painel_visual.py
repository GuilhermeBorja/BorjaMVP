import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos

def format_timedelta(delta):
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{days}d {hours}h {minutes}m {secs}s"

def calcular_tempo_total(processo, etapas):
    try:
        dt_criacao = datetime.datetime.strptime(processo["data_criacao"], "%d/%m/%Y %H:%M")
    except:
        return ""
    if etapas and all(etapa["data_termino_real"] for etapa in etapas):
        ultima = etapas[-1]["data_termino_real"]
        try:
            dt_ultima = datetime.datetime.strptime(ultima, "%d/%m/%Y %H:%M")
        except:
            return ""
        delta = dt_ultima - dt_criacao
    else:
        delta = datetime.datetime.now() - dt_criacao
    return format_timedelta(delta)

def calcular_status(processo, etapas):
    if etapas and all(etapa["data_termino_real"] for etapa in etapas):
        try:
            dt_ideal = datetime.datetime.strptime(processo["data_termino_ideal"], "%d/%m/%Y %H:%M")
            dt_ultima = datetime.datetime.strptime(etapas[-1]["data_termino_real"], "%d/%m/%Y %H:%M")
            if dt_ultima <= dt_ideal:
                return "Finalizado no prazo"
            else:
                return "Finalizado atrasado"
        except Exception:
            return "Finalizado"
    else:
        try:
            dt_ideal = datetime.datetime.strptime(processo["data_termino_ideal"], "%d/%m/%Y %H:%M")
            if datetime.datetime.now() > dt_ideal:
                return "Atrasado"
            else:
                return "No prazo"
        except Exception:
            return "Em andamento"

def delete_processo(processo_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM etapas WHERE processo_id=?", (processo_id,))
    cursor.execute("DELETE FROM processos WHERE id=?", (processo_id,))
    conn.commit()
    conn.close()

def calcular_tempo_etapa(etapas, data_criacao):
    tempos = []
    try:
        dt_prev = datetime.datetime.strptime(data_criacao, "%d/%m/%Y %H:%M")
    except:
        dt_prev = datetime.datetime.now()
    for idx, etapa in enumerate(etapas):
        if etapa["data_termino_real"]:
            try:
                dt_atual = datetime.datetime.strptime(etapa["data_termino_real"], "%d/%m/%Y %H:%M")
            except:
                dt_atual = datetime.datetime.now()
        else:
            dt_atual = datetime.datetime.now()
        delta = dt_atual - dt_prev
        tempos.append(format_timedelta(delta))
        if etapa["data_termino_real"]:
            dt_prev = datetime.datetime.strptime(etapa["data_termino_real"], "%d/%m/%Y %H:%M")
        else:
            dt_prev = datetime.datetime.now()
    return tempos

def painel_visual(user):
    st.header("Visualização de Processos")
    tabs = st.tabs(["Visualização Sintética", "Visualização Analítica"])
    
    filtros = filtros_processos()
    query = "SELECT * FROM processos WHERE 1=1"
    params = []
    if user["nivel"] == 1:
        query += " AND responsavel_geral=?"
        params.append(user["username"])
    if filtros["nome"]:
        query += " AND nome_processo LIKE ?"
        params.append(f"%{filtros['nome']}%")
    if filtros["responsavel"] and filtros["responsavel"] != "Todos":
        query += " AND responsavel_geral=?"
        params.append(filtros["responsavel"])
    if filtros["status"] and filtros["status"] != "Todos":
        query += " AND status LIKE ?"
        params.append(f"%{filtros['status']}%")
    if filtros["data_inicio"] and filtros["data_fim"]:
        data_inicio = filtros["data_inicio"].strftime("%d/%m/%Y")
        data_fim = filtros["data_fim"].strftime("%d/%m/%Y")
        query += " AND substr(data_criacao,1,10) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    processos = cursor.fetchall()
    conn.close()
    
    st.markdown(f"**Processos encontrados: {len(processos)}**")
    
    # Visualização Sintética
    with tabs[0]:
        if processos:
            st.markdown("### Processos")
            header_cols = st.columns([1, 3, 2, 2, 2, 2, 2, 2, 1])
            headers = ["ID", "Nome", "Resp. Geral", "Criação", "Término Ideal", "Término Real", "Tempo Total", "Status", "Ação"]
            for idx, title in enumerate(headers):
                header_cols[idx].markdown(f"<p style='text-align:center; font-weight:bold'>{title}</p>", unsafe_allow_html=True)
            for processo in processos:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (processo["id"],))
                etapas = cursor.fetchall()
                conn.close()
                tempo_total = calcular_tempo_total(processo, etapas)
                status_calc = calcular_status(processo, etapas)
                # Define cores para status
                if status_calc == "Atrasado":
                    status_colored = f"<span style='color:red'>{status_calc}</span>"
                elif status_calc == "Finalizado no prazo" or status_calc == "No prazo":
                    status_colored = f"<span style='color:green'>{status_calc}</span>"
                elif status_calc == "Finalizado atrasado":
                    status_colored = f"<span style='color:orange'>{status_calc}</span>"
                else:
                    status_colored = status_calc
                row_cols = st.columns([1, 3, 2, 2, 2, 2, 2, 2, 1])
                row_cols[0].markdown(f"<p style='text-align:center'>{processo['id']}</p>", unsafe_allow_html=True)
                row_cols[1].markdown(f"<p style='text-align:center'>{processo['nome_processo']}</p>", unsafe_allow_html=True)
                row_cols[2].markdown(f"<p style='text-align:center'>{processo['responsavel_geral']}</p>", unsafe_allow_html=True)
                row_cols[3].markdown(f"<p style='text-align:center'>{processo['data_criacao']}</p>", unsafe_allow_html=True)
                row_cols[4].markdown(f"<p style='text-align:center'>{processo['data_termino_ideal']}</p>", unsafe_allow_html=True)
                row_cols[5].markdown(f"<p style='text-align:center'>{processo['data_termino_real'] if processo['data_termino_real'] else ''}</p>", unsafe_allow_html=True)
                row_cols[6].markdown(f"<p style='text-align:center'>{tempo_total}</p>", unsafe_allow_html=True)
                row_cols[7].markdown(f"<p style='text-align:center'>{status_colored}</p>", unsafe_allow_html=True)
                if row_cols[8].button("Apagar", key=f"apagar_{processo['id']}"):
                    delete_processo(processo["id"])
                    st.rerun()
        else:
            st.info("Nenhum processo encontrado.")

    # Visualização Analítica
    with tabs[1]:
        st.subheader("Detalhamento Visual dos Processos")
        for processo in processos:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (processo["id"],))
            etapas = cursor.fetchall()
            conn.close()
            st.markdown(f"<h3 style='text-align:center'>{processo['nome_processo']}</h3>", unsafe_allow_html=True)
            tempos = calcular_tempo_etapa(etapas, processo["data_criacao"])
            etapas_html = ""
            for idx, etapa in enumerate(etapas):
                # Define cor da bolinha conforme se a etapa está concluída ou não
                if etapa["data_termino_real"]:
                    cor_etapa = "#28a745"  # Verde
                else:
                    cor_etapa = "#ffc107" if etapa["nome_etapa"] and etapa["responsavel_etapa"] else "#ffffff"
                etapas_html += f"""
                <div style="display:inline-block; text-align:center; margin:10px; vertical-align:middle;">
                    <div style="width:60px; height:60px; border-radius:50%; background-color:{cor_etapa}; 
                        display:flex; align-items:center; justify-content:center; border:2px solid #000; font-size:10px; overflow:hidden;">
                        <span style="word-break: break-word; text-align:center;">{etapa['nome_etapa'] if etapa['nome_etapa'] else 'N/A'}</span>
                    </div>
                    <div style="margin-top:5px; font-size:10px; text-align:center;">
                        {etapa['responsavel_etapa'] if etapa['responsavel_etapa'] else 'Sem resp.'}<br>
                        {tempos[idx]}
                    </div>
                </div>
                """
                if idx < len(etapas) - 1:
                    etapas_html += """<span style="font-size:24px; margin:0 5px; display:inline-flex; align-items:center;">&#8594;</span>"""
            st.markdown(f"<div style='text-align:center'>{etapas_html}</div>", unsafe_allow_html=True)
