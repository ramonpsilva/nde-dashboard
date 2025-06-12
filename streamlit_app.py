import pandas as pd
import plotly.express as px
import streamlit as st

@st.cache_data
def load_data():
    oferta = pd.read_excel('ofertaConsolidadaTratada.xlsx')
    semestres = oferta['semestre'].unique()
    departamentos = oferta.sort_values(by='ofertante')['ofertante'].unique()
    departamentos.sort()
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
    return oferta, semestres, departamentos, disciplinas, doi, df

# Load data ONCE (cached)
oferta, semestres, departamentos, disciplinas, doi, df = load_data()

def get_disciplina_options(depto):
    return disciplinas[disciplinas['ofertante'] == depto]['disciplina'].unique().tolist()

st.title("Análise de Ocupação de Disciplinas")

tab1, tab2 = st.tabs(["Ocupação Geral", "Departamentos Civil"])

with tab1:
    depto = st.selectbox("Selecione o departamento:", list(departamentos))
    disc_opts = get_disciplina_options(depto)
    disc = st.selectbox("Selecione a disciplina:", disc_opts)
    dfc = df[df['ofertante'] == depto]
    df1 = dfc[dfc['disciplina'] == disc]
    fig = px.line(df1, x='semestre', y=['vagas', 'ocupacao'], title=disc)
    fig.update_layout(legend_title_text='Ocupação')
    fig.update_traces({'name': 'vagas'}, selector={'name': 'vagas'})
    fig.update_traces({'name': 'ocupação'}, selector={'name': 'ocupacao'})
    fig.update_xaxes(zeroline=True)
    fig.update_yaxes(zeroline=True)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    depto_civil = st.radio("Selecione o departamento civil:", doi, horizontal=True)
    disc2_opts = get_disciplina_options(depto_civil)
    disc2 = st.selectbox("Selecione a disciplina:", disc2_opts, key="civil_disc")
    dfc2 = df[df['ofertante'] == depto_civil]
    df2 = dfc2[dfc2['disciplina'] == disc2]
    fig2 = px.line(df2, x='semestre', y=['vagas', 'ocupacao'], title=disc2)
    fig2.update_layout(legend_title_text='Ocupação')
    fig2.update_traces({'name': 'vagas'}, selector={'name': 'vagas'})
    fig2.update_traces({'name': 'ocupação'}, selector={'name': 'ocupacao'})
    fig2.update_xaxes(zeroline=True)
    fig2.update_yaxes(zeroline=True)
    st.plotly_chart(fig2, use_container_width=True)