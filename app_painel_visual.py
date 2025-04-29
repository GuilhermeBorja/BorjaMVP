import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos
from dateutil import tz

# 1.0 – Detecta o fuso horário do navegador (via JS) e converte para exibir localmente
def get_local_now():
    # pega o offset do navegador (em minutos) do componente JS
    offset = st.experimental_get_query_params().get("tz_offset", [0])[0]
    now_utc = datetime.datetime.utcnow().replace(tzinfo=tz.UTC)
    local = now_utc.astimezone(tz.tzoffset(None, -int(offset)*60))
    return local

def format_datetime(dt_str):
    # Espera formatos "DD/MM/YYYY HH:MM"
    try:
        dt = datetime.datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return dt_str

def format_timedelta(delta):
    d, s = delta.days, delta.seconds
    h = s//3600; m=(s%3600)//60; s=s%60
    return f"{d}d {h}h {m}m {s}s"

def calcular_tempo_total(processo, etapas):
    try:
        dt_cri = datetime.datetime.strptime(processo["data_criacao"], "%d/%m/%Y %H:%M")
    except:
        return ""
    if etapas and all(et["data_termino_real"] for et in etapas):
        ultima = etapas[-1]["data_termino_real"]
        dt_fin = datetime.datetime.strptime(ultima, "%d/%m/%Y %H:%M")
        delta = dt_fin - dt_cri
    else:
        delta = get_local_now() - dt_cri
    return format_timedelta(delta)

def delete_processo(pid):
    conn = get_connection(); c=conn.cursor()
    c.execute("DELETE FROM etapas WHERE processo_id=?", (pid,))
    c.execute("DELETE FROM processos WHERE id=?", (pid,))
    conn.commit(); conn.close()

def painel_visual(user):
    st.title("Visualização de Processos")
    # injeta script para pegar timezone offset (chama uma vez)
    st.markdown("""
      <script>
        var tz = new Date().getTimezoneOffset();
        window.parent.postMessage({func:'setTz', tz_offset:tz}, '*');
      </script>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Sintética", "Analítica"])

    filtros = filtros_processos()
    q = "SELECT * FROM processos WHERE 1=1"; params=[]
    # 2.0 – filtro data fim inclusivo
    if filtros["data_inicio"] and filtros["data_fim"]:
        di = filtros["data_inicio"].strftime("%d/%m/%Y")
        df = filtros["data_fim"] + datetime.timedelta(days=1)
        df = df.strftime("%d/%m/%Y")
        q += " AND substr(data_criacao,1,10)>=? AND substr(data_criacao,1,10)<=?"
        params += [di, df]
    # demais filtros...
    conn = get_connection(); c=conn.cursor()
    c.execute(q, tuple(params)); processos = c.fetchall(); conn.close()

    # 2.1 – formata ID com zeros à esquerda
    def fmt_id(i): return f"{i:02d}"

    # 2.2 – CSS para botão apagar não quebrar linha
    st.markdown("""
        <style>
          .apagar-btn button { white-space: nowrap; }
        </style>
    """, unsafe_allow_html=True)

    with tabs[0]:
        if not processos:
            st.info("Nenhum processo")
            return
        df = []
        for p in processos:
            c = get_connection().cursor()
            c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p["id"],))
            ets = c.fetchall(); c.connection.close()
            df.append({
                "ID": fmt_id(p["id"]),
                "Nome": p["nome_processo"],
                "Resp Geral": p["responsavel_geral"],
                "Criação": format_datetime(p["data_riacao"]),
                "Término Ideal": format_datetime(p["data_termino_ideal"]),
                "Término Real": format_datetime(p["data_termino_real"]) if p["data_termino_real"] else "",
                "Tempo Total": calcular_tempo_total(p, ets),
                "Status": p["status"]
            })
        tbl = pd.DataFrame(df)
        st.dataframe(tbl.style.set_properties(**{"text-align":"center"}).set_table_styles(
            [{"selector":"th","props":[("text-align","center")]}]
        ), use_container_width=True)

        for p in processos:
            css = '<div class="apagar-btn">' + st.button("Apagar", key=f"del_{p['id']}") and delete_processo(p["id"]) or "" + '</div>'
            st.markdown(css, unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Visualização Analítica")
        for p in processos:
            st.markdown(f"**{p['nome_processo']}**")
            c = get_connection().cursor()
            c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p["id"],))
            ets = c.fetchall(); c.connection.close()
            tempos = []
            dt_prev = datetime.datetime.strptime(p["data_criacao"], "%d/%m/%Y %H:%M")
            for et in ets:
                if et["data_termino_real"]:
                    dt_now = datetime.datetime.strptime(et["data_termino_real"], "%d/%m/%Y %H:%M")
                else:
                    dt_now = get_local_now()
                delta = dt_now - dt_prev
                tempos.append(format_timedelta(delta))
                dt_prev = dt_now
            # monta HTML centralizado
            html = ""
            for idx, et in enumerate(ets):
                cor = "#28a745" if et["data_termino_real"] else "#ffc107"
                html += f"""
                  <div style="display:inline-block;text-align:center;margin:10px;">
                    <div style="width:60px;height:60px;border-radius:50%;background:{cor};
                                display:flex;align-items:center;justify-content:center;">
                      <span style="font-size:10px;word-wrap:break-word;">{et['nome_etapa']}</span>
                    </div>
                    <div style="font-size:10px;text-align:center;">{et['responsavel_etapa']}<br>{tempos[idx]}</div>
                  </div>
                  {('<span style=\"display:inline-flex;align-items:center;font-size:24px;\">&#8594;</span>') if idx<len(ets)-1 else ''}
                """
            st.markdown(f"<div style='text-align:center'>{html}</div>", unsafe_allow_html=True)
