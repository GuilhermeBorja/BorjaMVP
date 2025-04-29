import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos

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
        return format_timedelta(dt1 - dt0)
    return format_timedelta(datetime.datetime.now() - dt0)

def delete_processo(pid):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM etapas WHERE processo_id=?", (pid,))
    c.execute("DELETE FROM processos WHERE id=?", (pid,))
    conn.commit(); conn.close()

def painel_visual(user):
    st.title("Visualização de Processos")
    filtros = filtros_processos()

    q, p = "SELECT * FROM processos WHERE 1=1", []
    if filtros["data_inicio"] and filtros["data_fim"]:
        d0 = filtros["data_inicio"].strftime("%d/%m/%Y")
        d1 = (filtros["data_fim"] + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        q += " AND substr(data_criacao,1,10)>=? AND substr(data_criacao,1,10)<=?"
        p += [d0, d1]

    conn = get_connection(); cur = conn.cursor()
    cur.execute(q, tuple(p)); procs = cur.fetchall(); conn.close()

    def fmt_id(x): return f"{x:02d}"
    st.markdown("<style>.btn-apagar button{white-space:nowrap;}</style>", unsafe_allow_html=True)

    st.subheader("Visualização Sintética")
    if procs:
        linhas = []
        for pr in procs:
            conn = get_connection(); c = conn.cursor()
            c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (pr["id"],))
            ets = c.fetchall(); conn.close()
            linhas.append({
                "ID": fmt_id(pr["id"]),
                "Nome": pr["nome_processo"],
                "Resp Geral": pr["responsavel_geral"],
                "Criação": pr["data_criacao"],
                "Término Ideal": pr["data_termino_ideal"],
                "Término Real": pr["data_termino_real"] or "",
                "Tempo Total": calcular_tempo_total(pr, ets),
                "Status": pr["status"]
            })
        df = pd.DataFrame(linhas)
        styled = df.style.set_properties(**{"text-align":"center"}).set_table_styles(
            [{"selector":"th","props":[("text-align","center")]}]
        )
        st.dataframe(styled, use_container_width=True)

        for pr in procs:
            if st.button("Apagar", key=f"del_{pr['id']}", css_class="btn-apagar"):
                delete_processo(pr["id"])
                st.experimental_rerun()
    else:
        st.info("Nenhum processo encontrado.")

    st.subheader("Visualização Analítica")
    for pr in procs:
        st.markdown(f"**{pr['nome_processo']}**")
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (pr["id"],))
        ets = c.fetchall(); conn.close()

        dt_prev = datetime.datetime.strptime(pr["data_criacao"], "%d/%m/%Y %H:%M")
        fragments = []
        for i, e in enumerate(ets):
            cor = "#28a745" if e["data_termino_real"] else "#ffc107"
            if e["data_termino_real"]:
                dt_now = datetime.datetime.strptime(e["data_termino_real"], "%d/%m/%Y %H:%M")
            else:
                dt_now = datetime.datetime.now()
            tempo = format_timedelta(dt_now - dt_prev)
            dt_prev = dt_now

            elem = f"""
            <div style="display:inline-block;margin:10px;text-align:center;">
              <div style="
                width:60px;height:60px;
                border-radius:50%;
                background:{cor};
                display:flex;align-items:center;justify-content:center;
              ">
                <span style="font-size:10px;word-wrap:break-word;">{e['nome_etapa']}</span>
              </div>
              <div style="font-size:10px;text-align:center;">
                {e['responsavel_etapa']}<br>{tempo}
              </div>
            </div>
            """
            fragments.append(elem)
            if i < len(ets) - 1:
                fragments.append(
                    '<span style="display:inline-flex;align-items:center;font-size:24px;">&#8594;</span>'
                )

        container = "<div style='text-align:center'>" + "".join(fragments) + "</div>"
        st.markdown(container, unsafe_allow_html=True)
