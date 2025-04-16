import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos

def calcular_status(processo):
    """Retorna o status calculado com base na data de término ideal e na data de término real."""
    hoje = datetime.datetime.now()
    if processo["data_termino_real"]:
        return "Concluído"
    else:
        try:
            dt_ideal = datetime.datetime.strptime(processo["data_termino_ideal"], "%Y-%m-%d")
            if hoje > dt_ideal:
                return "Atrasado"
            else:
                return "No prazo"
        except Exception:
            return processo["status"]

def painel_visual(user):
    st.header("Visualização de Processos")
    
    # Cria abas para seleção no topo
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
        query += " AND status=?"
        params.append(filtros["status"])
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
    
    with tabs[0]:
        # Visualização Sintética – usa uma tabela que agora preenche a largura da tela
        data = []
        for processo in processos:
            status_calc = calcular_status(processo)
            data.append({
                "ID": processo["id"],
                "Nome": processo["nome_processo"],
                "Resp. Geral": processo["responsavel_geral"],
                "Criação": processo["data_criacao"],
                "Término Ideal": processo["data_termino_ideal"],
                "Término Real": processo["data_termino_real"] if processo["data_termino_real"] else "",
                "Tempo Total": processo["tempo_total"],
                "Status": status_calc
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
    with tabs[1]:
        # Visualização Analítica – exibe cada processo com seus estágios representados por bolinhas grandes (60px)
        st.subheader("Detalhamento Visual dos Processos")
        for processo in processos:
            status_calc = calcular_status(processo)
            # Determina a cor da bolinha do processo com base no status geral
            if status_calc == "Concluído":
                cor_processo = "#28a745"  # Verde
            elif status_calc == "Atrasado":
                cor_processo = "#dc3545"  # Vermelho/alarme
            else:
                cor_processo = "#ffc107"  # Amarelo
            
            st.markdown(f"### {processo['nome_processo']}  — Status: **{status_calc}**")
            # Recupera as etapas
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM etapas WHERE processo_id=?", (processo["id"],))
            etapas = cursor.fetchall()
            conn.close()
            
            # Monta a linha visual com as etapas em formato de bolinhas interligadas por setas
            etapas_html = ""
            for idx, etapa in enumerate(etapas, start=1):
                # Escolhe a cor da bolinha conforme a etapa estar concluída ou não
                if etapa["data_termino_real"]:
                    cor_etapa = "#28a745"
                else:
                    # Se alguma informação estiver faltando, adota branco; caso contrário, amarelo
                    if etapa["nome_etapa"] and etapa["responsavel_etapa"]:
                        cor_etapa = "#ffc107"
                    else:
                        cor_etapa = "#ffffff"
                # Tempo gasto pode ser calculado com base em atualizações (aqui é exibido como valor armazenado)
                tempo = etapa["tempo_gasto"]
                etapas_html += f"""
                <div style="display:inline-block; text-align:center; margin:10px;">
                    <div style="width:60px; height:60px; border-radius:50%; background-color:{cor_etapa}; 
                        line-height:60px; font-size:12px; border:2px solid #000;">
                        {etapa['nome_etapa'] if etapa['nome_etapa'] else 'N/A'}
                    </div>
                    <div style="margin-top:5px; font-size:11px;">
                        {etapa['responsavel_etapa'] if etapa['responsavel_etapa'] else 'Sem resp.'}<br>
                        Tempo: {tempo}h
                    </div>
                </div>
                """
                if idx < len(etapas):
                    etapas_html += """<span style="font-size:24px; margin:0 5px;">&#8594;</span>"""
            st.markdown(etapas_html, unsafe_allow_html=True)
