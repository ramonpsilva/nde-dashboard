# Done with the help of gitHub Copilot, with some adjustments and optimizations by me.
# The code is a Streamlit app for analyzing the occupancy of courses offered by different departments at a university.
# It allows users to select a department, a course, and visualize the occupancy data either as a sum of all
# classes or by individual class. The data is loaded from an Excel file and cached for performance.
# The app uses Plotly for interactive visualizations.
# -rps April, 29, 2026

import io
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    # oferta = pd.read_excel('ofertaConsolidadaTratada.xlsx')
    oferta = pd.read_excel('ofertaConsolidada20261.xlsx')
    semestres = oferta['semestre'].unique()
    departamentos = sorted(oferta.sort_values(by='ofertante')['ofertante'].unique())
    oferta['disciplina'] = oferta.apply(lambda row: row.codigo + ": " + row.nome, axis=1)
    disciplinas = pd.DataFrame(oferta.drop(columns=['curso', 'professor', 'ch_prof', 'horario', 'insc']))
    disciplinas.reset_index(inplace=True, drop=True)
    disciplinas.sort_values(by='disciplina', inplace=True)
    doi = ['EES', 'EHR', 'EMC', 'ESA', 'ETG']

    # calculo geral de disciplinas para gráficos de ocupação
    df = pd.DataFrame(columns=['semestre', 'disciplina', 'ofertante', 'vagas', 'ocupacao', 'nt'])
    for sem in semestres:
        disciplinas_sem = oferta[oferta['semestre'] == sem]
        for cur in departamentos:
            disciplina_depto = disciplinas_sem[disciplinas_sem['ofertante'] == cur]
            disciplina_codigos = disciplina_depto['codigo'].unique()
            for cod in disciplina_codigos:
                somaocupa = disciplina_depto.loc[disciplina_depto['codigo'] == cod, 'ocupacao'].sum()
                somavagas = disciplina_depto.loc[disciplina_depto['codigo'] == cod, 'vagas'].sum()
                somaturmas = disciplina_depto.loc[disciplina_depto['codigo'] == cod, 'turma'].count()
                d = disciplina_depto.loc[disciplina_depto['codigo'] == cod]['disciplina'].unique().tolist()[0]
                df.loc[len(df.index)] = [sem, d, cur, somavagas, somaocupa, somaturmas]
    df.sort_values(by='semestre', inplace=True)
    return semestres, departamentos, disciplinas, doi, df, oferta

# Load data ONCE (cached)
semestres, departamentos, disciplinas, doi, df, oferta = load_data()
semestres_sorted = sorted(df['semestre'].unique().tolist())

def get_disciplina_options(depto):
    return disciplinas[disciplinas['ofertante'] == depto]['disciplina'].unique().tolist()

def df_to_excel_bytes(dataframe):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    return buffer.getvalue()

st.title("Análise de Ocupação de Disciplinas")

tab1, tab2 = st.tabs(["Ocupação Geral", "Departamentos Civil"])

with tab1:
    col_depto, col_disc = st.columns(2)
    depto = col_depto.selectbox("Selecione o departamento:", list(departamentos))
    disc_opts = get_disciplina_options(depto)
    disc = col_disc.selectbox("Selecione a disciplina:", disc_opts)
    col_modo, col_sem = st.columns(2)
    modo = col_modo.radio("Visualização:", ["Soma geral das turmas", "Por turma"], horizontal=True)
    sem_range = col_sem.select_slider("Intervalo de semestres:", options=semestres_sorted, value=(semestres_sorted[0], semestres_sorted[-1]))
    if modo == "Soma geral das turmas":
        dfc = df[df['ofertante'] == depto]
        df1 = dfc[dfc['disciplina'] == disc]
        df1 = df1[(df1['semestre'] >= sem_range[0]) & (df1['semestre'] <= sem_range[1])]
        fig = px.line(df1, x='semestre', y=['vagas', 'ocupacao'], title=disc)
        fig.update_layout(legend_title_text='Ocupação')
        fig.update_traces({'name': 'vagas'}, selector={'name': 'vagas'})
        fig.update_traces({'name': 'ocupação'}, selector={'name': 'ocupacao'})
        fig.update_xaxes(zeroline=True)
        fig.update_yaxes(zeroline=True, rangemode="tozero")
        col1, _ = st.columns([4, 1])
        col1.plotly_chart(fig, use_container_width=True)
        st.subheader("Estatísticas da disciplina")
        media_vagas = df1['vagas'].mean()
        media_ocupa = df1['ocupacao'].mean()
        taxa_ocupa = (media_ocupa / media_vagas * 100) if media_vagas > 0 else 0
        periodos = df1['semestre'].nunique()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Média de Vagas", f"{media_vagas:.1f}")
        c2.metric("Média de Ocupação", f"{media_ocupa:.1f}")
        c3.metric("Taxa de Ocupação", f"{taxa_ocupa:.1f}%")
        c4.metric("Períodos Analisados", periodos)
        nome_arquivo = disc.replace(' ', '_') + '.xlsx'
        st.download_button("Salvar dados em Excel", data=df_to_excel_bytes(df1), file_name=nome_arquivo, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        disc_oferta = oferta[(oferta['ofertante'] == depto) & (oferta['disciplina'] == disc)]
        turmas_disp = sorted(disc_oferta['turma'].dropna().unique().tolist(), key=str)
        turmas_sel = st.multiselect("Selecione as turmas:", turmas_disp, default=turmas_disp)
        if turmas_sel:
            df_turmas = disc_oferta[disc_oferta['turma'].isin(turmas_sel)][['semestre', 'turma', 'ocupacao', 'vagas']].copy()
            df_turmas['turma'] = df_turmas['turma'].astype(str)
            df_turmas = df_turmas[(df_turmas['semestre'] >= sem_range[0]) & (df_turmas['semestre'] <= sem_range[1])]
            df_turmas.sort_values(by='semestre', inplace=True)
            fig = px.line(df_turmas, x='semestre', y='ocupacao', color='turma', title=disc, markers=True)
            fig.update_layout(legend_title_text='Turma')
            fig.update_xaxes(zeroline=True)
            fig.update_yaxes(zeroline=True, rangemode="tozero")
            col1, _ = st.columns([4, 1])
            col1.plotly_chart(fig, use_container_width=True)
            st.subheader("Estatísticas da disciplina")
            media_vagas_t = df_turmas['vagas'].mean()
            media_ocupa_t = df_turmas['ocupacao'].mean()
            taxa_ocupa_t = (media_ocupa_t / media_vagas_t * 100) if media_vagas_t > 0 else 0
            periodos_t = df_turmas['semestre'].nunique()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Média de Vagas", f"{media_vagas_t:.1f}")
            c2.metric("Média de Ocupação", f"{media_ocupa_t:.1f}")
            c3.metric("Taxa de Ocupação", f"{taxa_ocupa_t:.1f}%")
            c4.metric("Períodos Analisados", periodos_t)
            nome_arquivo = disc.replace(' ', '_') + '.xlsx'
            st.download_button("Salvar dados em Excel", data=df_to_excel_bytes(df_turmas), file_name=nome_arquivo, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.info("Selecione ao menos uma turma para visualizar.")

with tab2:
    col_depto2, col_disc2 = st.columns(2)
    depto_civil = col_depto2.radio("Selecione o departamento:", doi, horizontal=True, key="depto_civil")
    disc2_opts = get_disciplina_options(depto_civil)
    disc2 = col_disc2.selectbox("Selecione a disciplina:", disc2_opts, key="civil_disc")
    col_modo2, col_sem2 = st.columns(2)
    modo2 = col_modo2.radio("Visualização:", ["Soma geral das turmas", "Por turma"], horizontal=True, key="modo2")
    sem_range2 = col_sem2.select_slider("Intervalo de semestres:", options=semestres_sorted, value=(semestres_sorted[0], semestres_sorted[-1]), key="sem_range2")
    if modo2 == "Soma geral das turmas":
        dfc2 = df[df['ofertante'] == depto_civil]
        df2 = dfc2[dfc2['disciplina'] == disc2]
        df2 = df2[(df2['semestre'] >= sem_range2[0]) & (df2['semestre'] <= sem_range2[1])]
        fig2 = px.line(df2, x='semestre', y=['vagas', 'ocupacao'], title=disc2)
        fig2.update_layout(legend_title_text='Ocupação')
        fig2.update_traces({'name': 'vagas'}, selector={'name': 'vagas'})
        fig2.update_traces({'name': 'ocupação'}, selector={'name': 'ocupacao'})
        fig2.update_xaxes(zeroline=True)
        fig2.update_yaxes(zeroline=True, rangemode="tozero")
        col2, _ = st.columns([4, 1])
        col2.plotly_chart(fig2, use_container_width=True)
        st.subheader("Estatísticas da disciplina")
        media_vagas = df2['vagas'].mean()
        media_ocupa = df2['ocupacao'].mean()
        taxa_ocupa = (media_ocupa / media_vagas * 100) if media_vagas > 0 else 0
        periodos = df2['semestre'].nunique()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Média de Vagas", f"{media_vagas:.1f}")
        c2.metric("Média de Ocupação", f"{media_ocupa:.1f}")
        c3.metric("Taxa de Ocupação", f"{taxa_ocupa:.1f}%")
        c4.metric("Períodos Analisados", periodos)
        nome_arquivo = disc2.replace(' ', '_') + '.xlsx'
        st.download_button("Salvar dados em Excel", data=df_to_excel_bytes(df2), file_name=nome_arquivo, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        disc2_oferta = oferta[(oferta['ofertante'] == depto_civil) & (oferta['disciplina'] == disc2)]
        turmas2_disp = sorted(disc2_oferta['turma'].dropna().unique().tolist(), key=str)
        turmas2_sel = st.multiselect("Selecione as turmas:", turmas2_disp, default=turmas2_disp, key="turmas2")
        if turmas2_sel:
            df_turmas2 = disc2_oferta[disc2_oferta['turma'].isin(turmas2_sel)][['semestre', 'turma', 'ocupacao', 'vagas']].copy()
            df_turmas2['turma'] = df_turmas2['turma'].astype(str)
            df_turmas2 = df_turmas2[(df_turmas2['semestre'] >= sem_range2[0]) & (df_turmas2['semestre'] <= sem_range2[1])]
            df_turmas2.sort_values(by='semestre', inplace=True)
            fig2 = px.line(df_turmas2, x='semestre', y='ocupacao', color='turma', title=disc2, markers=True)
            fig2.update_layout(legend_title_text='Turma')
            fig2.update_xaxes(zeroline=True)
            fig2.update_yaxes(zeroline=True, rangemode="tozero")
            col2, _ = st.columns([4, 1])
            col2.plotly_chart(fig2, use_container_width=True)
            st.subheader("Estatísticas da disciplina")
            media_vagas2 = df_turmas2['vagas'].mean()
            media_ocupa2 = df_turmas2['ocupacao'].mean()
            taxa_ocupa2 = (media_ocupa2 / media_vagas2 * 100) if media_vagas2 > 0 else 0
            periodos2 = df_turmas2['semestre'].nunique()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Média de Vagas", f"{media_vagas2:.1f}")
            c2.metric("Média de Ocupação", f"{media_ocupa2:.1f}")
            c3.metric("Taxa de Ocupação", f"{taxa_ocupa2:.1f}%")
            c4.metric("Períodos Analisados", periodos2)
            nome_arquivo = disc2.replace(' ', '_') + '.xlsx'
            st.download_button("Salvar dados em Excel", data=df_to_excel_bytes(df_turmas2), file_name=nome_arquivo, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.info("Selecione ao menos uma turma para visualizar.")