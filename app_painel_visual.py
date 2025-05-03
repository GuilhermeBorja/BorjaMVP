import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos

def get_local_now():
    # Get current time in local timezone
    return datetime.datetime.now()

def format_timedelta(delta):
    d, s = delta.days, delta.seconds
    h, m = s//3600, (s%3600)//60
    s = s%60
    return f"{d}d {h}h {m}m {s}s"

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

def delete_processo(pid):
    conn = get_connection(); c=conn.cursor()
    c.execute("DELETE FROM etapas WHERE processo_id=?", (pid,))
    c.execute("DELETE FROM processos WHERE id=?", (pid,))
    conn.commit(); conn.close()

def painel_visual(user):
    st.header("Visualização de Processos")
    filtros = filtros_processos()

    query = "SELECT * FROM processos WHERE 1=1"
    params = []
    if filtros["data_inicio"] and filtros["data_fim"]:
        d0 = filtros["data_inicio"].strftime("%d/%m/%Y")
        d1 = (filtros["data_fim"] + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        query += " AND substr(data_criacao,1,10)>=? AND substr(data_criacao,1,10)<=?"
        params += [d0, d1]

    conn = get_connection(); cur=conn.cursor()
    cur.execute(query, tuple(params))
    procs = cur.fetchall(); conn.close()

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
                    ets = c.fetchall(); c.connection.close()
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
                        if st.button("✏️", key=f"edit_{p['id']}", help="Editar processo"):
                            st.session_state.pagina = "atualizar"
                            st.session_state.processo_para_editar = p["id"]
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_{p['id']}", help="Apagar processo"):
                            delete_processo(p["id"])
                            st.rerun()
        else:
            st.info("Nenhum processo encontrado.")

    with tab2:
        for p in procs:
            st.markdown(f"### {p['nome_processo']}")
            c = get_connection().cursor()
            c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p["id"],))
            ets = c.fetchall(); c.connection.close()
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
