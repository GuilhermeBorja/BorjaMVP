import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos

# Formatação de duração

def format_timedelta(delta):
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{days}d {hours}h {minutes}m {secs}s"

# Cálculo de tempo total

def calcular_tempo_total(processo, etapas):
    try:
        dt_cri = datetime.datetime.strptime(processo["data_criacao"], "%d/%m/%Y %H:%M")
    except:
        return ""
    if etapas and all(et["data_termino_real"] for et in etapas):
        dt_fin = datetime.datetime.strptime(etapas[-1]["data_termino_real"], "%d/%m/%Y %H:%M")
        delta = dt_fin - dt_cri
    else:
        delta = datetime.datetime.now() - dt_cri
    return format_timedelta(delta)

# Exclusão de processo

def delete_processo(pid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM etapas WHERE processo_id=?", (pid,))
    cursor.execute("DELETE FROM processos WHERE id=?", (pid,))
    conn.commit()
    conn.close()

# Função principal

def painel_visual(user):
    st.title("Visualização de Processos")

    # Filtros na sidebar
    filtros = filtros_processos()
    query = "SELECT * FROM processos WHERE 1=1"
    params = []

    # Ajuste do filtro de data (data_fim inclusivo)
    if filtros["data_inicio"] and filtros["data_fim"]:
        di = filtros["data_inicio"].strftime("%d/%m/%Y")
        df = (filtros["data_fim"] + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        query += " AND substr(data_criacao,1,10)>=? AND substr(data_criacao,1,10)<=?"
        params += [di, df]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    processos = cursor.fetchall()
    conn.close()

    # Função para formatar ID com dois dígitos
    def fmt_id(x):
        return f"{x:02d}"

    # CSS para botão apagar
    st.markdown(
        """
        <style>
          .btn-apagar button { white-space: nowrap; }
        </style>
        """, unsafe_allow_html=True
    )

    # Aba Sintética
    st.subheader("Visualização Sintética")
    if processos:
        data = []
        for p in processos:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p["id"],))
            ets = c.fetchall()
            conn.close()
            data.append({
                "ID": fmt_id(p["id"]),
                "Nome": p["nome_processo"],
                "Resp. Geral": p["responsavel_geral"],
                "Criação": p["data_criacao"],
                "Término Ideal": p["data_termino_ideal"],
                "Término Real": p["data_termino_real"] or "",
                "Tempo Total": calcular_tempo_total(p, ets),
                "Status": p["status"]
            })
        df = pd.DataFrame(data)
        styled = (
            df.style
              .set_properties(**{"text-align": "center"})
              .set_table_styles([{"selector": "th", "props": [("text-align", "center")] }])
        )
        st.dataframe(styled, use_container_width=True)

        for p in processos:
            if st.button("Apagar", key=f"del_{p['id']}", css_class="btn-apagar"):
                delete_processo(p["id"])
                st.experimental_rerun()
    else:
        st.info("Nenhum processo encontrado.")

    # Aba Analítica
    st.subheader("Visualização Analítica")
    for p in processos:
        st.markdown(f"**{p['nome_processo']}**")
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p["id"],))
        ets = c.fetchall()
        conn.close()

        dt_prev = datetime.datetime.strptime(p["data_criacao"], "%d/%m/%Y %H:%M")
        html = "<div style='text-align:center'>"
        for idx, et in enumerate(ets):
            cor = "#28a745" if et["data_termino_real"] else "#ffc107"
            if et["data_termino_real"]:
                dt_now = datetime.datetime.strptime(et["data_termino_real"], "%d/%m/%Y %H:%M")
            else:
                dt_now = datetime.datetime.now()
            tempo = format_timedelta(dt_now - dt_prev)
            dt_prev = dt_now
            html += f"""
              <div style="display:inline-block;margin:10px;text-align:center;">
                <div style="width:60px;height:60px;border-radius:50%;background-color:{cor};display:flex;align-items:center;justify-content:center;">
                  <span style="font-size:10px;word-wrap:break-word;">{et['nome_etapa']}</span>
                </div>
                <div style="font-size:10px;text-align:center;">{et['responsavel_etapa']}<br>{tempo}</div>
              </div>
            """
            if idx < len(ets) - 1:
                html += "<span style='display:inline-flex;align-items:center;font-size:24px;'>&#8594;</span>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
