import streamlit as st
import pandas as pd
import datetime
from db_connect import get_connection
from app_filtros import filtros_processos


def format_timedelta(delta):
    days, seconds = delta.days, delta.seconds
    h = seconds // 3600; m = (seconds % 3600) // 60; s = seconds % 60
    return f"{days}d {h}h {m}m {s}s"


def calcular_tempo_total(processo, etapas):
    try:
        dt_cri = datetime.datetime.strptime(processo['data_criacao'], "%d/%m/%Y %H:%M")
    except:
        return ""
    if etapas and all(et['data_termino_real'] for et in etapas):
        dt_fin = datetime.datetime.strptime(etapas[-1]['data_termino_real'], "%d/%m/%Y %H:%M")
        return format_timedelta(dt_fin - dt_cri)
    return format_timedelta(datetime.datetime.now() - dt_cri)


def delete_processo(pid):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("DELETE FROM etapas WHERE processo_id=?", (pid,))
    cursor.execute("DELETE FROM processos WHERE id=?", (pid,))
    conn.commit(); conn.close()


def painel_visual(user):
    st.title("Visualização de Processos")

    filtros = filtros_processos()
    q, params = "SELECT * FROM processos WHERE 1=1", []
    if filtros['data_inicio'] and filtros['data_fim']:
        di = filtros['data_inicio'].strftime("%d/%m/%Y")
        df = (filtros['data_fim'] + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        q += " AND substr(data_criacao,1,10)>=? AND substr(data_criacao,1,10)<=?"
        params += [di, df]

    conn = get_connection(); cursor = conn.cursor()
    cursor.execute(q, tuple(params)); processos = cursor.fetchall(); conn.close()

    def fmt_id(i): return f"{i:02d}"

    st.markdown("<style>.btn-apagar button{white-space:nowrap;}</style>", unsafe_allow_html=True)

    st.subheader("Visualização Sintética")
    if processos:
        df = pd.DataFrame([
            {
                'ID': fmt_id(p['id']),
                'Nome': p['nome_processo'],
                'Resp. Geral': p['responsavel_geral'],
                'Criação': p['data_criacao'],
                'Término Ideal': p['data_termino_ideal'],
                'Término Real': p['data_termino_real'] or '',
                'Tempo Total': calcular_tempo_total(p, []),
                'Status': p['status']
            }
            for p in processos
        ])
        styled = (df.style.set_properties(**{'text-align':'center'})
                     .set_table_styles([{'selector':'th','props': [('text-align','center')]}]))
        st.dataframe(styled, use_container_width=True)
        for p in processos:
            if st.button('Apagar', key=f"del_{p['id']}", css_class='btn-apagar'):
                delete_processo(p['id']); st.experimental_rerun()
    else:
        st.info('Nenhum processo encontrado.')

    st.subheader('Visualização Analítica')
    for p in processos:
        st.markdown(f"**{p['nome_processo']}**")
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT * FROM etapas WHERE processo_id=? ORDER BY id", (p['id'],))
        ets = c.fetchall(); conn.close()
        dt_prev = datetime.datetime.strptime(p['data_criacao'], "%d/%m/%Y %H:%M")
        html = "<div style='text-align:center'>"
        for idx, et in enumerate(ets):
            cor = '#28a745' if et['data_termino_real'] else '#ffc107'
            dt_now = datetime.datetime.strptime(et['data_termino_real'], "%d/%m/%Y %H:%M") if et['data_termino_real'] else datetime.datetime.now()
            tempo = format_timedelta(dt_now - dt_prev); dt_prev = dt_now
            html += f"<div style='display:inline-block;margin:10px;text-align:center;'>"\
