import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos

def calcular_tempo_total(processo, etapas):
    try:
        dt_criacao = datetime.datetime.strptime(processo["data_criacao"], "%Y-%m-%d %H:%M:%S")
    except:
        return ""
    if etapas and all(etapa["data_termino_real"] for etapa in etapas):
        # Processo finalizado: usa a data de término real da última etapa
        ultima = etapas[-1]["data_termino_real"]
        try:
            dt_ultima = datetime.datetime.strptime(ultima, "%Y-%m-%d %H:%M:%S")
        except:
            return ""
        delta = dt_ultima - dt_criacao
    else:
        delta = datetime.datetime.now() - dt_criacao
    return round(delta.total_seconds()/3600, 1)

def calcular_status(processo, etapas):
    if etapas and all(etapa["data_termino_real"] for etapa in etapas):
        try:
            dt_ideal = datetime.datetime.strptime(processo["data_termino_ideal"], "%Y-%m-%d")
            ultima = etapas[-1]["data_termino_real"]
            dt_ultima = datetime.datetime.strptime(ultima, "%Y-%m-%d %H:%M:%S")
            if dt_ultima <= dt_ideal:
                return "Finalizado no prazo"
            else:
                return "Finalizado atrasado"
        except Exception:
            return "Finalizado"
    else:
        try:
            dt_ideal = datetime.datetime.strptime(processo["data_termino_ideal"], "%Y-%m-%d")
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
        dt_prev = datetime.datetime.strptime(data_criacao, "%Y-%m-%d %H:%M:%S")
    except:
        dt_prev = datetime.datetime.now()
    for idx, etapa in enumerate(etapas):
        if etapa["data_termino_real"]:
            try:
                dt_atual = datetime.datetime.strptime(etapa["data_termino_real"], "%Y-%m-%d %H:%M:%S")
            except:
                dt_atual = datetime.datetime.now()
        else:
            dt_atual = datetime.datetime.now()
        delta = dt_atual - dt_prev
        tempos.append(round(delta.total_seconds()/3600, 1))
        if etapa["data_termino_real"]:
            dt_prev = datetime.datetime.strptime(etapa["data_termino_real"], "%Y-%m-%d %H:%M:%S")
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
        data_inicio = filtros["data_inicio"].strftime("%Y-%m-%d")
        data_fim = filtros["data_fim"].strftime("%Y-%m-%d")
        query += " AND date(data_criacao) BETWEEN ? AND ?"
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
            # Cria cabeçalhos customizados sem coluna vazia
            header_cols = st.columns([1, 3, 2, 2, 2, 2, 2, 2, 1])
            headers = ["ID", "Nome", "Resp. Geral", "Criação", "Término Ideal", "Término Real", "Tempo Total (h)", "Status", "Ação"]
            for idx, title in enumerate(headers):
                header_cols[idx].markdown(f"**{title}**")
            for processo in processos:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (processo["id"],))
                etapas = cursor.fetchall()
                conn.close()
                tempo_total = calcular_tempo_total(processo, etapas)
                status_calc = calcular_status(processo, etapas)
                row_cols = st.columns([1, 3, 2, 2, 2, 2, 2, 2, 1])
                row_cols[0].write(processo["id"])
                row_cols[1].write(processo["nome_processo"])
                row_cols[2].write(processo["responsavel_geral"])
                row_cols[3].write(processo["data_criacao"])
                row_cols[4].write(processo["data_termino_ideal"])
                row_cols[5].write(processo["data_termino_real"] if processo["data_termino_real"] else "")
                row_cols[6].write(tempo_total)
                row_cols[7].write(status_calc)
                if row_cols[8].button("Apagar", key=f"apagar_{processo['id']}"):
                    delete_processo(processo["id"])
                    st.experimental_rerun()
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
            status_calc = calcular_status(processo, etapas)
            st.markdown(f"### {processo['nome_processo']} — Status: **{status_calc}**")
            tempos = calcular_tempo_etapa(etapas, processo["data_criacao"])
            etapas_html = ""
            for idx, etapa in enumerate(etapas):
                if etapa["data_termino_real"]:
                    cor_etapa = "#28a745"  # Concluída: Verde
                else:
                    if etapa["nome_etapa"] and etapa["responsavel_etapa"]:
                        cor_etapa = "#ffc107"
                    else:
                        cor_etapa = "#ffffff"
                etapas_html += f"""
                <div style="display:inline-block; text-align:center; margin:10px;">
                    <div style="width:60px; height:60px; border-radius:50%; background-color:{cor_etapa}; 
                        display:flex; align-items:center; justify-content:center; border:2px solid #000; font-size:10px; overflow:hidden;">
                        <span style="word-wrap: break-word;">{etapa['nome_etapa'] if etapa['nome_etapa'] else 'N/A'}</span>
                    </div>
                    <div style="margin-top:5px; font-size:10px;">
                        {etapa['responsavel_etapa'] if etapa['responsavel_etapa'] else 'Sem resp.'}<br>
                        Tempo: {tempos[idx]}h
                    </div>
                </div>
                """
                if idx < len(etapas) - 1:
                    etapas_html += """<span style="font-size:24px; margin:0 5px;">&#8594;</span>"""
            st.markdown(etapas_html, unsafe_allow_html=True)
