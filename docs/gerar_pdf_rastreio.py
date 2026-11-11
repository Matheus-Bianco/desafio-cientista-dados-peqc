# -*- coding: utf-8 -*-
"""
Gera o documento de RASTREIO (PDF): passo a passo do que foi feito, arquivo por
arquivo, com significado, como foi feito, caracteristicas e exemplo real de cada
tabela, mais a matriz de conformidade (pedido x entregue).

Os exemplos de tabela sao extraidos simulando o pipeline no DuckDB sobre os
Parquet locais (identicos ao bucket), para refletir o que cada model produz.
"""
import os
import math
import duckdb
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, XPreformatted, KeepTogether, Image,
)

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "..", "data").replace("\\", "/")
SEED = os.path.join(AQUI, "..", "seeds", "seed_educacao__disciplinas.csv").replace("\\", "/")
SAIDA = os.path.join(AQUI, "Desafio-RMI-Rastreio.pdf")

# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
AZUL = colors.HexColor("#1e3a8a")
AZUL2 = colors.HexColor("#2563eb")
CINZA = colors.HexColor("#475569")
CINZA_CLARO = colors.HexColor("#f1f5f9")
VERDE = colors.HexColor("#15803d")
VERDE_BG = colors.HexColor("#dcfce7")
AMARELO_BG = colors.HexColor("#fef9c3")
VERMELHO = colors.HexColor("#b91c1c")
VERMELHO_BG = colors.HexColor("#fee2e2")
AZUL_BG = colors.HexColor("#eff6ff")
BORDA = colors.HexColor("#cbd5e1")

ss = getSampleStyleSheet()
st_title = ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=25,
                          textColor=AZUL, leading=29, alignment=TA_LEFT)
st_sub = ParagraphStyle("st", parent=ss["Normal"], fontSize=12.5, textColor=CINZA, leading=17)
st_h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=17,
                       textColor=AZUL, spaceBefore=14, spaceAfter=7, leading=20)
st_h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
                       textColor=AZUL2, spaceBefore=11, spaceAfter=4, leading=15)
st_h3 = ParagraphStyle("h3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=10,
                       textColor=colors.HexColor("#0f172a"), spaceBefore=6, spaceAfter=2)
st_body = ParagraphStyle("b", parent=ss["Normal"], fontSize=10, leading=14.5, alignment=TA_JUSTIFY,
                         spaceAfter=5, textColor=colors.HexColor("#1e293b"))
st_bullet = ParagraphStyle("bu", parent=st_body, leftIndent=14, bulletIndent=3, spaceAfter=2)
st_small = ParagraphStyle("sm", parent=st_body, fontSize=8.5, textColor=CINZA, alignment=TA_LEFT)
st_th = ParagraphStyle("th", parent=st_body, fontName="Helvetica-Bold", fontSize=8.8,
                       textColor=colors.white, alignment=TA_LEFT, spaceAfter=0, leading=11)
st_td = ParagraphStyle("td", parent=st_body, fontSize=8.5, leading=11, alignment=TA_LEFT, spaceAfter=0)
st_cell = ParagraphStyle("ce", parent=st_body, fontSize=6.9, leading=8.4, alignment=TA_LEFT, spaceAfter=0)
st_cellh = ParagraphStyle("ceh", parent=st_cell, fontName="Helvetica-Bold", textColor=colors.white)
st_toc = ParagraphStyle("toc", parent=st_body, fontSize=10.5, leading=16, spaceAfter=1, alignment=TA_LEFT)
st_meta = ParagraphStyle("meta", parent=st_td, fontSize=8.6)
st_metab = ParagraphStyle("metab", parent=st_meta, fontName="Helvetica-Bold")

import re
def _prep(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<font face="Courier" size="8.5">\1</font>', t)
    return t

def P(t, s=st_body): return Paragraph(_prep(t), s)
def H1(t): return Paragraph(_prep(t), st_h1)
def H2(t): return Paragraph(_prep(t), st_h2)
def H3(t): return Paragraph(_prep(t), st_h3)
def BU(items):
    return [Paragraph(_prep(i), st_bullet, bulletText="\u2022") for i in items]

STATUS_COR = {"OK": (VERDE_BG, VERDE), "PARCIAL": (AMARELO_BG, colors.HexColor("#a16207")),
              "PENDENTE": (VERMELHO_BG, VERMELHO)}

def tabela(dados, larguras, header=True, status_col=None):
    linhas = []
    for r, row in enumerate(dados):
        linha = []
        for cidx, cell in enumerate(row):
            if r == 0 and header:
                linha.append(Paragraph(_prep(str(cell)), st_th))
            else:
                linha.append(Paragraph(_prep(str(cell)), st_td))
        linhas.append(linha)
    t = Table(linhas, colWidths=larguras, repeatRows=1 if header else 0)
    est = [("GRID", (0, 0), (-1, -1), 0.4, BORDA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO])]
    if header:
        est.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
    if status_col is not None:
        for r in range(1, len(dados)):
            s = dados[r][status_col]
            if s in STATUS_COR:
                bg, _ = STATUS_COR[s]
                est.append(("BACKGROUND", (status_col, r), (status_col, r), bg))
    t.setStyle(TableStyle(est))
    return t

def callout(titulo, texto, bg=AZUL_BG, border=AZUL2):
    conteudo = [Paragraph(_prep(titulo), ParagraphStyle("bt", parent=st_body, fontName="Helvetica-Bold",
                                                        textColor=border, spaceAfter=2))]
    for t in ([texto] if isinstance(texto, str) else texto):
        conteudo.append(Paragraph(_prep(t), st_body))
    tb = Table([[conteudo]], colWidths=[16.5 * cm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg),
                            ("LINEBEFORE", (0, 0), (0, -1), 3, border),
                            ("BOX", (0, 0), (-1, -1), 0.4, BORDA),
                            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return tb

def code_block(text):
    safe = text.strip("\n").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    inner = XPreformatted(safe, ParagraphStyle("c", parent=ss["Code"], fontName="Courier",
                                               fontSize=7.8, leading=10, textColor=colors.HexColor("#0f172a")))
    tb = Table([[inner]], colWidths=[16.5 * cm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                            ("BOX", (0, 0), (-1, -1), 0.6, BORDA),
                            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return tb

def fmt(v):
    if v is None:
        return "(nulo)"
    if isinstance(v, float) and math.isnan(v):
        return "(nulo)"
    s = str(v)
    if len(s) > 18:
        s = s[:16] + "\u2026"
    return s

def df_to_table(df):
    cols = list(df.columns)
    ncols = len(cols)
    larg = (16.5 * cm) / ncols
    head = [Paragraph(_prep(str(c)), st_cellh) for c in cols]
    linhas = [head]
    for _, row in df.iterrows():
        linhas.append([Paragraph(_prep(fmt(row[c])), st_cell) for c in cols])
    t = Table(linhas, colWidths=[larg] * ncols, repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, BORDA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), AZUL2),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
                           ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t

def cols_table(cols):
    dados = [["Coluna", "Tipo", "Descrição"]]
    for nome, tipo, desc in cols:
        dados.append([nome, tipo, desc])
    return tabela(dados, [4.2 * cm, 2.8 * cm, 9.5 * cm])

# ----------------------------------------------------------------------------
# Emulacao do pipeline no DuckDB
# ----------------------------------------------------------------------------
con = duckdb.connect()
def t(nome): return f"read_parquet('{DATA}/{nome}')"

con.execute(f"""
create or replace view stg_alunos as
select lower(to_hex(id_aluno)) aluno_id, id_turma turma_id,
       nullif(trim(faixa_etaria),'') faixa_etaria, bairro bairro_id from {t('aluno')}
""")
con.execute(f"create or replace view stg_escolas as select id_escola escola_id, bairro bairro_id from {t('escola')}")
con.execute(f"""
create or replace view stg_matriculas as
select lower(to_hex(id_aluno)) aluno_id, id_turma turma_id, ano ano_letivo from {t('turma')}
""")
con.execute(f"""
create or replace view stg_frequencia as
with renamed as (
  select id_escola escola_id, lower(to_hex(id_aluno)) aluno_id, id_turma turma_id,
         strptime(data_inicio,'%Y-%m-%d')::date periodo_data_inicio,
         strptime(data_fim,'%Y-%m-%d')::date periodo_data_fim,
         disciplina disciplina_codigo,
         case disciplina when 'disciplina_1' then 'Português' when 'disciplina_2' then 'Ciências'
              when 'disciplina_3' then 'Inglês' when 'disciplina_4' then 'Matemática' end disciplina,
         frequencia percentual_frequencia
  from {t('frequencia')}),
dedup as (select *, row_number() over (partition by aluno_id,turma_id,escola_id,periodo_data_inicio,periodo_data_fim,disciplina_codigo order by percentual_frequencia desc) rn from renamed)
select * exclude(rn) from dedup where rn=1
""")
con.execute(f"""
create or replace view stg_avaliacoes as
with base as (
  select lower(to_hex(id_aluno)) aluno_id, id_turma turma_id, cast(bimestre as integer) bimestre,
         frequencia frequencia_bimestre_origem, disciplina_1,disciplina_2,disciplina_3,disciplina_4 from {t('avaliacao')}),
lng as (
  select aluno_id,turma_id,bimestre,frequencia_bimestre_origem,'disciplina_1' disciplina_codigo,disciplina_1 nota from base
  union all select aluno_id,turma_id,bimestre,frequencia_bimestre_origem,'disciplina_2',disciplina_2 from base
  union all select aluno_id,turma_id,bimestre,frequencia_bimestre_origem,'disciplina_3',disciplina_3 from base
  union all select aluno_id,turma_id,bimestre,frequencia_bimestre_origem,'disciplina_4',disciplina_4 from base),
m as (select *, case disciplina_codigo when 'disciplina_1' then 'Português' when 'disciplina_2' then 'Ciências'
           when 'disciplina_3' then 'Inglês' when 'disciplina_4' then 'Matemática' end disciplina from lng),
dedup as (select *, row_number() over (partition by aluno_id,turma_id,bimestre,disciplina_codigo order by nota desc) rn from m)
select aluno_id,turma_id,bimestre,frequencia_bimestre_origem,disciplina_codigo,disciplina,nota from dedup where rn=1
""")
con.execute("""
create or replace view int_aluno_frequencia as
with fb as (select distinct aluno_id,turma_id,bimestre, frequencia_bimestre_origem fbv from stg_avaliacoes where frequencia_bimestre_origem is not null and not isnan(frequencia_bimestre_origem)),
fa as (select aluno_id, count(*) n_bimestres_com_frequencia, avg(fbv) media_frequencia, min(fbv) min_frequencia, max(fbv) max_frequencia from fb group by aluno_id),
fr as (select aluno_id, count(*) n_registros_frequencia, avg(percentual_frequencia) media_frequencia_registros from stg_frequencia group by aluno_id),
ep as (select aluno_id, escola_id from (select aluno_id, escola_id, row_number() over (partition by aluno_id order by count(*) desc, escola_id) rn from stg_frequencia group by aluno_id, escola_id) where rn=1)
select a.aluno_id, a.faixa_etaria, a.turma_id turma_id_matricula, ep.escola_id,
       fa.n_bimestres_com_frequencia, round(fa.media_frequencia,2) media_frequencia,
       round(fa.min_frequencia,2) min_frequencia, round(fa.max_frequencia,2) max_frequencia,
       fr.n_registros_frequencia, round(fr.media_frequencia_registros,2) media_frequencia_registros,
       (fa.media_frequencia < 75) flag_absenteismo_cronico
from stg_alunos a
left join fa on a.aluno_id=fa.aluno_id
left join fr on a.aluno_id=fr.aluno_id
left join ep on a.aluno_id=ep.aluno_id
""")
con.execute("""
create or replace view int_aluno_desempenho as
select aluno_id, turma_id, count(*) n_notas, count(distinct bimestre) n_bimestres,
  round(avg(nota),2) media_geral,
  round(avg(case when disciplina='Português' then nota end),2) media_portugues,
  round(avg(case when disciplina='Ciências' then nota end),2) media_ciencias,
  round(avg(case when disciplina='Inglês' then nota end),2) media_ingles,
  round(avg(case when disciplina='Matemática' then nota end),2) media_matematica,
  (avg(nota) >= 6) flag_aprovado_media
from stg_avaliacoes where nota is not null group by aluno_id, turma_id
""")
con.execute("""
create or replace view mart_absenteismo as
with agg as (
  select e.bairro_id, af.escola_id, count(*) n_alunos,
    count(*) filter (where af.media_frequencia is not null) n_alunos_com_frequencia,
    count(*) filter (where af.flag_absenteismo_cronico) n_alunos_absenteismo_cronico,
    round(avg(af.media_frequencia),2) media_frequencia_regiao,
    round(min(af.media_frequencia),2) pior_frequencia_media_aluno,
    round(avg(af.media_frequencia_registros),2) media_frequencia_registros_regiao
  from int_aluno_frequencia af left join stg_escolas e on af.escola_id=e.escola_id
  where af.escola_id is not null group by e.bairro_id, af.escola_id)
select *, round(n_alunos_absenteismo_cronico / nullif(n_alunos_com_frequencia,0),4) taxa_absenteismo_cronico
from agg order by taxa_absenteismo_cronico desc, media_frequencia_regiao asc
""")
con.execute("""
create or replace view mart_desempenho_turma as
with tam as (select turma_id, count(*) n_alunos_matriculados from stg_matriculas group by turma_id),
dt as (select turma_id, count(distinct aluno_id) n_alunos_avaliados, round(avg(media_geral),2) media_geral_turma,
         round(avg(media_portugues),2) media_portugues, round(avg(media_ciencias),2) media_ciencias,
         round(avg(media_matematica),2) media_matematica,
         round(avg(case when flag_aprovado_media then 1 else 0 end),4) taxa_aprovacao_media
       from int_aluno_desempenho group by turma_id)
select t.turma_id, t.n_alunos_matriculados,
  case when t.n_alunos_matriculados<=5 then '01. Ate 5' when t.n_alunos_matriculados<=10 then '02. 6 a 10'
       when t.n_alunos_matriculados<=20 then '03. 11 a 20' when t.n_alunos_matriculados<=30 then '04. 21 a 30'
       else '05. Mais de 30' end faixa_tamanho_turma,
  dt.n_alunos_avaliados, dt.media_geral_turma, dt.media_portugues, dt.media_ciencias, dt.media_matematica, dt.taxa_aprovacao_media
from tam t left join dt on t.turma_id=dt.turma_id order by t.n_alunos_matriculados desc
""")

def get_count(view):
    return con.execute(f"select count(*) from {view}").fetchall()[0][0]

def get_sample(sql, n=3):
    return con.execute(sql + f" limit {n}").df()

# ----------------------------------------------------------------------------
# Conteudo
# ----------------------------------------------------------------------------
E = []

def entity(nome, arquivo, formato, grao, linhas, proposito, como, notas, cols, sample_sql):
    bloco = [H2(nome)]
    meta = tabela([
        ["Arquivo", arquivo],
        ["Formato", formato],
        ["Grão (1 linha =)", grao],
        ["Linhas", f"{linhas:,}".replace(",", ".")],
    ], [3.6 * cm, 12.9 * cm], header=False)
    bloco.append(meta)
    bloco.append(Spacer(1, 3))
    bloco.append(P("**O que é / significa:** " + proposito))
    bloco.append(P("**Como foi feito:** " + como))
    if notas:
        bloco.append(P("**Características e qualidade:** " + notas))
    E.append(KeepTogether(bloco))
    E.append(H3("Exemplo (amostra real)"))
    E.append(df_to_table(get_sample(sample_sql)))
    E.append(Spacer(1, 3))
    E.append(H3("Colunas"))
    E.append(cols_table(cols))
    E.append(Spacer(1, 8))

# ---------- CAPA ----------
E.append(Spacer(1, 3.2 * cm))
E.append(Paragraph("Desafio Técnico RMI", st_sub))
E.append(Spacer(1, 0.2 * cm))
E.append(Paragraph("Documento de Rastreio da Solução", st_title))
E.append(Spacer(1, 0.35 * cm))
E.append(Paragraph("Passo a passo do que foi construído: arquivo por arquivo, o que significa, "
                   "como foi feito, características e exemplo real de cada tabela. Inclui a matriz "
                   "de conformidade (o que foi pedido, o que atendemos e o que ficou pendente).", st_sub))
E.append(Spacer(1, 1.0 * cm))
E.append(tabela([["Autor", "Matheus Bianco"], ["Projeto", "desafio-rmi-ds"],
                 ["Como ler", "Use como checklist de revisão e mapa para novos insights."]],
                [3.6 * cm, 12.9 * cm], header=False))
E.append(Spacer(1, 0.6 * cm))
E.append(callout("Como os exemplos foram gerados",
                 "As amostras e contagens de cada model foram extraídas simulando o pipeline no "
                 "DuckDB sobre os Parquet locais (idênticos ao bucket, verificado por checksum MD5). "
                 "Refletem o que o dbt produz no BigQuery; os IDs hexadecimais aparecem truncados "
                 "por espaço."))
E.append(PageBreak())

# ---------- SUMARIO ----------
E.append(H1("Sumário"))
for s in ["1. Conformidade: o que foi pedido x o que foi entregue",
          "2. Visão geral do pipeline e mapa de arquivos",
          "3. Camada de fontes (dados brutos)",
          "4. Camada de staging",
          "5. Camada intermediate",
          "6. Camada de marts",
          "7. Painel de resultados (visualização dos marts)",
          "8. Seeds, macros, testes, CI e scripts",
          "9. Decisões e achados (rastreabilidade do raciocínio)",
          "10. O que NÃO foi feito e pendências",
          "Anexo: como os números foram verificados"]:
    E.append(Paragraph(_prep(s), st_toc))
E.append(PageBreak())

# ---------- 1. CONFORMIDADE ----------
E.append(H1("1. Conformidade: o que foi pedido x o que foi entregue"))
E.append(P("Legenda de status: **OK** (atendido), **PARCIAL** (feito, com ressalva) e "
           "**PENDENTE** (não feito)."))
E.append(H2("Parte 1: Projeto dbt e Modelagem"))
E.append(tabela([
    ["Item pedido", "Status", "Onde / observação"],
    ["Projeto dbt configurado (dbt_project.yml, sources, estrutura)", "OK", "dbt_project.yml, packages.yml, sources definidas"],
    ["Staging para >=4 tabelas (limpeza, tipagem, nulos, schema.yml)", "OK", "5 tabelas em staging + _educacao__models.yml"],
    ["Intermediate >=1 combinando fontes", "OK", "2 models intermediate"],
    ["Mart >=1 respondendo pergunta de gestor + schema.yml", "OK", "2 marts (table) + breve análise no README"],
    ["dbt run executa sem erros", "OK", "dbt build no BigQuery (projeto exerciciodesafio): 9 models criados, 0 erros"],
], [7.6 * cm, 2.0 * cm, 6.9 * cm], status_col=1))
E.append(H2("Parte 2: Testes e Qualidade"))
E.append(tabela([
    ["Item pedido", "Status", "Onde / observação"],
    ["Testes genéricos (unique, not_null, accepted_values, relationships)", "OK", "Nos schema.yml de staging, intermediate e marts"],
    [">=2 testes singular / customizados de regra de negócio", "OK", "3 testes em tests/ + 1 teste genérico customizado"],
    ["dbt test passando", "OK", "PASS=62, WARN=1 (órfãos de turma, planejado), ERROR=0"],
], [7.6 * cm, 2.0 * cm, 6.9 * cm], status_col=1))
E.append(H2("Parte 3: Documentação e Análise"))
E.append(tabela([
    ["Item pedido", "Status", "Onde / observação"],
    ["README (setup, lineage, decisões, trade-offs)", "OK", "README.md"],
    ["Análise exploratória (opcional / diferencial)", "OK", "notebooks/eda.ipynb"],
], [7.6 * cm, 2.0 * cm, 6.9 * cm], status_col=1))
E.append(H2("Diferenciais sugeridos"))
E.append(tabela([
    ["Diferencial", "Status", "Observação"],
    ["dbt packages", "PARCIAL", "dbt_utils usado; dbt_expectations e codegen declarados mas não usados em testes"],
    ["freshness nas sources", "OK", "Configurado (baseado em metadados)"],
    ["tags", "OK", "Tags por camada no dbt_project.yml"],
    ["exposures", "OK", "Exposure do painel de gestão"],
    ["hooks", "PENDENTE", "Não utilizado"],
    ["data contracts", "PENDENTE", "Listado como próximo passo"],
    ["CI com dbt build (GitHub Actions)", "PARCIAL", "Workflow pronto; roda de fato após configurar secrets do GCP"],
], [6.0 * cm, 2.0 * cm, 8.5 * cm], status_col=1))
E.append(PageBreak())

# ---------- 2. MAPA ----------
E.append(H1("2. Visão geral do pipeline e mapa de arquivos"))
E.append(P("O fluxo: dados brutos no BigQuery (raw) -> **staging** (limpeza, 1 view por fonte) -> "
           "**intermediate** (combinações e métricas) -> **marts** (tabelas finais de consumo). "
           "Testes e documentação acompanham cada camada."))
E.append(tabela([
    ["Fontes (raw)", "Staging (view)", "Intermediate (ephemeral)", "Marts (table)"],
    ["aluno", "stg_educacao__alunos", "int_educacao__aluno_frequencia", "mart_educacao__absenteismo_regiao"],
    ["escola", "stg_educacao__escolas", "int_educacao__aluno_desempenho", "mart_educacao__desempenho_por_turma"],
    ["turma", "stg_educacao__matriculas", "", ""],
    ["avaliacao", "stg_educacao__avaliacoes", "", ""],
    ["frequencia", "stg_educacao__frequencia", "", ""],
], [3.3 * cm, 4.3 * cm, 4.7 * cm, 4.2 * cm]))
E.append(Spacer(1, 5))
E.append(H2("Todos os arquivos do projeto"))
E.append(tabela([
    ["Arquivo", "Formato", "Papel"],
    ["dbt_project.yml", "YAML", "Configuração central: materializações, tags, vars de negócio"],
    ["packages.yml", "YAML", "Pacotes dbt (dbt_utils, dbt_expectations, codegen)"],
    ["profiles.yml.example", "YAML", "Modelo de conexão ao BigQuery (dev e ci)"],
    ["requirements.txt", "texto", "Dependências Python"],
    [".gitignore", "texto", "Ignora dados, credenciais, artefatos"],
    ["scripts/load_to_bigquery.py", "Python", "Carrega os Parquet do bucket para o BigQuery"],
    ["scripts/load_to_bigquery.sh", "Shell", "Mesma ingestão via bq CLI"],
    ["seeds/seed_educacao__disciplinas.csv", "CSV", "De/para de código de disciplina"],
    ["macros/nome_disciplina.sql", "SQL/Jinja", "Traduz código de disciplina (DRY)"],
    ["macros/generic_tests/test_proporcao_nulos_abaixo_de.sql", "SQL/Jinja", "Teste genérico customizado"],
    ["models/staging/educacao/*.sql", "SQL", "5 models de limpeza"],
    ["models/staging/educacao/_educacao__sources.yml", "YAML", "Fontes + freshness"],
    ["models/staging/educacao/_educacao__models.yml", "YAML", "Descrições e testes do staging"],
    ["models/intermediate/educacao/*.sql", "SQL", "2 models de métricas"],
    ["models/marts/educacao/*.sql", "SQL", "2 marts de consumo"],
    ["models/marts/educacao/_marts_educacao__exposures.yml", "YAML", "Exposure (painel)"],
    ["tests/*.sql", "SQL", "3 testes singular de regra de negócio"],
    ["notebooks/eda.ipynb", "Jupyter", "Análise exploratória"],
    [".github/workflows/ci.yml", "YAML", "CI (dbt build)"],
    ["README.md", "Markdown", "Documentação técnica"],
    ["docs/Desafio-RMI-Guia-101.pdf", "PDF", "Guia didático"],
    ["docs/Desafio-RMI-Rastreio.pdf", "PDF", "Este documento"],
    ["docs/amostras/*", "CSV/XLSX", "Amostras das tabelas brutas"],
], [6.6 * cm, 1.9 * cm, 8.0 * cm]))
E.append(PageBreak())

# ---------- 3. FONTES ----------
E.append(H1("3. Camada de fontes (dados brutos)"))
E.append(P("São as 5 tabelas Parquet do bucket `gs://case_vagas/rmi`, carregadas para um dataset "
           "`raw` no BigQuery. No dbt elas são declaradas como `sources`. Abaixo, cada uma com "
           "exemplo e características."))

entity("Fonte: aluno", "gs://case_vagas/rmi/aluno", "Parquet", "um aluno", get_count(t("aluno")),
       "Cadastro de alunos anonimizado (faixa etária, bairro em hash).",
       "Carregada direto do bucket para o BigQuery. id_aluno é BYTES (hash de 17 bytes).",
       "97.044 alunos únicos. bairro tem ~0,07% de nulos. id_aluno exibido aqui em hexadecimal.",
       [("id_aluno", "BYTES", "ID do aluno (hash). Vira hexadecimal no staging."),
        ("id_turma", "INT64", "Turma de matrícula."),
        ("faixa_etaria", "STRING", "0-5, 6-10, 11-14, 15-17, 18+."),
        ("bairro", "INT64", "Hash do bairro (com nulos).")],
       f"select lower(to_hex(id_aluno)) id_aluno, id_turma, faixa_etaria, bairro from {t('aluno')}")

entity("Fonte: escola", "gs://case_vagas/rmi/escola", "Parquet", "uma escola", get_count(t("escola")),
       "Cadastro de unidades escolares.",
       "Carregada direto do bucket. Chaves em hash.",
       "1.558 escolas únicas, em 169 bairros distintos. Sem nulos relevantes.",
       [("id_escola", "INT64", "ID da escola (hash)."), ("bairro", "INT64", "Hash do bairro da escola.")],
       f"select * from {t('escola')}")

entity("Fonte: turma", "gs://case_vagas/rmi/turma", "Parquet", "um aluno (matrícula)", get_count(t("turma")),
       "Apesar do nome, é a tabela de MATRÍCULAS: liga aluno a turma. Não traz série nem turno.",
       "Carregada direto do bucket. Uma linha por aluno.",
       "97.044 linhas (1 por aluno), 17.311 turmas. ano sempre 2000 (anonimizado).",
       [("ano", "INT64", "Ano letivo (fixo 2000)."), ("id_turma", "INT64", "Turma."),
        ("id_aluno", "BYTES", "Aluno matriculado.")],
       f"select ano, id_turma, lower(to_hex(id_aluno)) id_aluno from {t('turma')}")

entity("Fonte: avaliacao", "gs://case_vagas/rmi/avaliacao", "Parquet", "um aluno/turma/bimestre",
       get_count(t("avaliacao")),
       "Notas por bimestre em formato LARGO (uma coluna por disciplina). Contém também a frequência "
       "geral do bimestre (campo com variância, usado no absenteísmo).",
       "Carregada direto do bucket. Precisa de UNPIVOT no staging para virar formato longo.",
       "221.687 linhas. disciplina_3 (Inglês) 100% nula. frequência preenchida em ~99%. ~34 duplicatas de grão.",
       [("id_aluno", "BYTES", "Aluno."), ("id_turma", "INT64", "Turma."),
        ("frequencia", "FLOAT64", "Frequência geral do bimestre (0-100, com sinal)."),
        ("bimestre", "STRING", "1 a 4."),
        ("disciplina_1..4", "FLOAT64", "Notas: Português, Ciências, Inglês, Matemática.")],
       f"select lower(to_hex(id_aluno)) id_aluno, id_turma, frequencia, bimestre, disciplina_1, disciplina_2, disciplina_3, disciplina_4 from {t('avaliacao')}")

entity("Fonte: frequencia", "gs://case_vagas/rmi/frequencia", "Parquet",
       "aluno/turma/escola/período/disciplina", get_count(t("frequencia")),
       "Registros de frequência por período e disciplina. É a maior tabela.",
       "Carregada direto do bucket. Datas como texto; anonimizadas no ano 2000.",
       "2,7 milhões de linhas. Percentual travado entre 97% e 100% (sem variância). id_turma com ~12% de órfãos; id_aluno e id_escola conciliam 100%. ~2,6 mil duplicatas.",
       [("id_escola", "INT64", "Escola."), ("id_aluno", "BYTES", "Aluno."),
        ("id_turma", "INT64", "Turma (~12% órfãos)."),
        ("data_inicio/fim", "STRING", "Período (ano 2000)."),
        ("disciplina", "STRING", "disciplina_1..4."),
        ("frequencia", "FLOAT64", "Percentual (97-100).")],
       f"select id_escola, lower(to_hex(id_aluno)) id_aluno, id_turma, data_inicio, data_fim, disciplina, frequencia from {t('frequencia')}")
E.append(PageBreak())

# ---------- 4. STAGING ----------
E.append(H1("4. Camada de staging"))
E.append(P("Uma view por fonte. Objetivo: limpar, renomear, tipar e padronizar, sem lógica de "
           "negócio. Materializadas como **view** (leves, sempre refletem a fonte)."))

entity("stg_educacao__alunos", "models/staging/educacao/stg_educacao__alunos.sql", "SQL (view)",
       "um aluno", get_count("stg_alunos"),
       "Dimensão de alunos limpa.",
       "Converte id_aluno de BYTES para STRING hexadecimal (to_hex), renomeia colunas e aplica "
       "nullif/trim na faixa etária.",
       "Chave aluno_id única e não nula (testado).",
       [("aluno_id", "STRING", "Hex do aluno (chave)."), ("turma_id", "INT64", "Turma."),
        ("faixa_etaria", "STRING", "Faixa etária."), ("bairro_id", "INT64", "Bairro (hash).")],
       "select * from stg_alunos")

entity("stg_educacao__escolas", "models/staging/educacao/stg_educacao__escolas.sql", "SQL (view)",
       "uma escola", get_count("stg_escolas"),
       "Dimensão de escolas limpa.",
       "Renomeia as colunas para o padrão do projeto.",
       "escola_id única e não nula (testado).",
       [("escola_id", "INT64", "Chave da escola."), ("bairro_id", "INT64", "Bairro da escola.")],
       "select * from stg_escolas")

entity("stg_educacao__matriculas", "models/staging/educacao/stg_educacao__matriculas.sql", "SQL (view)",
       "um aluno/turma", get_count("stg_matriculas"),
       "Matrículas (origem: fonte turma), renomeada para refletir a semântica real.",
       "Converte id_aluno para hex e renomeia ano para ano_letivo.",
       "aluno_id único (1 matrícula por aluno); ano_letivo sempre 2000 (testado).",
       [("aluno_id", "STRING", "Aluno."), ("turma_id", "INT64", "Turma."),
        ("ano_letivo", "INT64", "Ano (2000).")],
       "select * from stg_matriculas")

entity("stg_educacao__frequencia", "models/staging/educacao/stg_educacao__frequencia.sql", "SQL (view)",
       "aluno/turma/escola/período/disciplina", get_count("stg_frequencia"),
       "Frequência limpa e deduplicada.",
       "Converte datas (texto para date), traduz o código de disciplina para nome (macro), e remove "
       "duplicatas de grão com row_number().",
       "Grão único após dedup (testado). percentual_frequencia entre 0 e 100.",
       [("escola_id", "INT64", "Escola."), ("aluno_id", "STRING", "Aluno."),
        ("turma_id", "INT64", "Turma."), ("periodo_data_inicio/fim", "DATE", "Período."),
        ("disciplina_codigo", "STRING", "disciplina_1..4."), ("disciplina", "STRING", "Nome legível."),
        ("percentual_frequencia", "FLOAT64", "0-100.")],
       "select * from stg_frequencia")

entity("stg_educacao__avaliacoes", "models/staging/educacao/stg_educacao__avaliacoes.sql", "SQL (view)",
       "aluno/turma/bimestre/disciplina", get_count("stg_avaliacoes"),
       "Notas normalizadas de LARGO para LONGO (uma linha por disciplina).",
       "Aplica UNPIVOT (mantendo nulos) sobre disciplina_1..4, traduz o nome, carrega a frequência "
       "do bimestre e remove duplicatas de grão.",
       "nota pode ser nula (ausência legítima). Inclui a coluna frequencia_bimestre_origem (fonte do absenteísmo).",
       [("aluno_id", "STRING", "Aluno."), ("turma_id", "INT64", "Turma."),
        ("bimestre", "INT64", "1 a 4."), ("frequencia_bimestre_origem", "FLOAT64", "Freq. geral do bimestre."),
        ("disciplina_codigo", "STRING", "Código."), ("disciplina", "STRING", "Nome."),
        ("nota", "FLOAT64", "0-10 ou nula.")],
       "select * from stg_avaliacoes")
E.append(PageBreak())

# ---------- 5. INTERMEDIATE ----------
E.append(H1("5. Camada intermediate"))
E.append(P("Combina as fontes limpas e cria métricas por aluno. Materializada como **ephemeral** "
           "(vira CTE embutida nos marts, sem criar tabela física)."))

entity("int_educacao__aluno_frequencia", "models/intermediate/educacao/int_educacao__aluno_frequencia.sql",
       "SQL (ephemeral)", "um aluno", get_count("int_aluno_frequencia"),
       "Frequência consolidada por aluno. A frequência COM SINAL vem do campo de frequência da "
       "avaliação; a da tabela frequencia entra como contraste. Marca o absenteísmo crônico.",
       "Junta por aluno_id (chave confiável). Média bimestral da avaliação, média por registro da "
       "tabela frequencia, e escola predominante (maior contagem de registros).",
       "1 linha por aluno. flag_absenteismo_cronico = media_frequencia < 75. media_frequencia nula "
       "para alunos sem avaliação.",
       [("aluno_id", "STRING", "Aluno."), ("faixa_etaria", "STRING", "Faixa."),
        ("escola_id", "INT64", "Escola predominante."),
        ("media_frequencia", "FLOAT64", "Média bimestral (com sinal)."),
        ("media_frequencia_registros", "FLOAT64", "Contraste (tabela frequencia)."),
        ("flag_absenteismo_cronico", "BOOL", "média < 75%.")],
       "select aluno_id, faixa_etaria, escola_id, n_bimestres_com_frequencia, media_frequencia, media_frequencia_registros, flag_absenteismo_cronico from int_aluno_frequencia where media_frequencia is not null")

entity("int_educacao__aluno_desempenho", "models/intermediate/educacao/int_educacao__aluno_desempenho.sql",
       "SQL (ephemeral)", "um aluno/turma", get_count("int_aluno_desempenho"),
       "Desempenho acadêmico consolidado por aluno, com médias por disciplina.",
       "A partir das avaliações (ignorando notas nulas), calcula média geral e média por disciplina.",
       "media_geral de 0 a 10. flag_aprovado_media = média >= 6. Inglês fica nulo (sem notas).",
       [("aluno_id", "STRING", "Aluno."), ("turma_id", "INT64", "Turma."),
        ("n_notas", "INT64", "Qtd. de notas."), ("media_geral", "FLOAT64", "0-10."),
        ("media_portugues/ciencias/matematica", "FLOAT64", "Por disciplina."),
        ("flag_aprovado_media", "BOOL", "média >= 6.")],
       "select aluno_id, turma_id, n_notas, media_geral, media_portugues, media_ciencias, media_matematica, flag_aprovado_media from int_aluno_desempenho")
E.append(PageBreak())

# ---------- 6. MARTS ----------
E.append(H1("6. Camada de marts"))
E.append(P("As tabelas finais, que respondem perguntas de gestor. Materializadas como **table** "
           "para consulta rápida."))

entity("mart_educacao__absenteismo_regiao", "models/marts/educacao/mart_educacao__absenteismo_regiao.sql",
       "SQL (table)", "uma escola", get_count("mart_absenteismo"),
       "Taxa de absenteísmo crônico (frequência média bimestral < 75%) por escola e região.",
       "Agrega int_aluno_frequencia por escola/bairro; usa a frequência com sinal para o flag; "
       "expõe também a frequência por registro como contraste.",
       "Resultado acionável: ~10,4% de absenteísmo geral, variando de 0% a 33% entre escolas.",
       [("bairro_id", "INT64", "Região."), ("escola_id", "INT64", "Escola (chave)."),
        ("n_alunos", "INT64", "Alunos da escola."),
        ("n_alunos_absenteismo_cronico", "INT64", "Qtd. com absenteísmo."),
        ("taxa_absenteismo_cronico", "FLOAT64", "Proporção 0-1."),
        ("media_frequencia_regiao", "FLOAT64", "Média da escola.")],
       "select bairro_id, escola_id, n_alunos, n_alunos_com_frequencia, n_alunos_absenteismo_cronico, taxa_absenteismo_cronico, media_frequencia_regiao from mart_absenteismo where n_alunos_com_frequencia >= 20")

entity("mart_educacao__desempenho_por_turma", "models/marts/educacao/mart_educacao__desempenho_por_turma.sql",
       "SQL (table)", "uma turma", get_count("mart_desempenho_turma"),
       "Desempenho médio por turma cruzado com o tamanho da turma.",
       "Calcula o tamanho da turma (matrículas) e junta com as médias de desempenho por turma.",
       "Permite analisar tamanho x desempenho. Turmas sem avaliação ficam com médias nulas.",
       [("turma_id", "INT64", "Turma (chave)."), ("n_alunos_matriculados", "INT64", "Tamanho."),
        ("faixa_tamanho_turma", "STRING", "Faixa de tamanho."),
        ("media_geral_turma", "FLOAT64", "Média 0-10."),
        ("taxa_aprovacao_media", "FLOAT64", "Proporção aprovados.")],
       "select turma_id, n_alunos_matriculados, faixa_tamanho_turma, n_alunos_avaliados, media_geral_turma, taxa_aprovacao_media from mart_desempenho_turma where n_alunos_avaliados is not null")
E.append(PageBreak())

# ---------- 7. PAINEL ----------
E.append(H1("7. Painel de resultados (visualização dos marts)"))
E.append(P("Os marts alimentam um painel executivo de gestão (HTML + Chart.js, também publicado como "
           "web app em Google Apps Script). Ele resume os indicadores da rede em uma leitura rápida: "
           "KPIs, o contraste entre as duas frequências, a distribuição de escolas por faixa de "
           "absenteísmo e o desempenho por tamanho de turma. Por serem dados anonimizados e estáveis, "
           "os mesmos marts podem ser conectados em um clique ao Looker Studio (nativo do BigQuery)."))
_IMG = os.path.join(AQUI, "painel", "img")
def figura(nome, legenda):
    p = os.path.join(_IMG, nome)
    if not os.path.exists(p):
        return
    w = 16.5 * cm
    h = w * 863.0 / 1278.0
    E.append(KeepTogether([Image(p, width=w, height=h), P(legenda, st_small)]))
    E.append(Spacer(1, 10))
figura("painel_topo.png", "Figura 1. Cabeçalho, faixa de KPIs da rede e início dos gráficos de frequência.")
figura("painel_full.png", "Figura 2. As duas frequências, faixas de absenteísmo, desempenho por tamanho de turma e média por disciplina.")
E.append(P("Os números do painel vêm do dataset `rmi_dev_marts` no BigQuery. A consolidação está em "
           "`docs/painel/exportar_consolidado.py` e o painel (HTML + projeto Apps Script) em `docs/painel/`.", st_small))
E.append(PageBreak())

# ---------- 8. APOIO ----------
E.append(H1("8. Seeds, macros, testes, CI e scripts"))
E.append(H2("Seed"))
E.append(P("`seeds/seed_educacao__disciplinas.csv` (CSV): de/para dos códigos de disciplina. "
           "Carregado no warehouse pelo `dbt seed`."))
E.append(df_to_table(con.execute(f"select * from read_csv_auto('{SEED}')").df()))
E.append(H2("Macros"))
E.append(tabela([
    ["Arquivo", "O que faz"],
    ["macros/nome_disciplina.sql", "Traduz disciplina_1..4 para nome legível (reuso/DRY no SQL)"],
    ["macros/generic_tests/test_proporcao_nulos_abaixo_de.sql", "Teste genérico customizado: tolera uma fração de nulos e avisa se piorar"],
], [7.2 * cm, 9.3 * cm]))
E.append(H2("Testes de regra de negócio (tests/)"))
E.append(tabela([
    ["Teste", "Regra verificada", "Passa quando"],
    ["assert_periodo_frequencia_coerente", "data_inicio nunca maior que data_fim", "Nenhuma linha retornada"],
    ["assert_aluno_frequencia_sem_duplicatas", "Grão da frequência único após dedup", "Nenhuma linha retornada"],
    ["assert_todo_aluno_com_nota_tem_matricula", "Nota exige matrícula correspondente", "Nenhuma linha retornada"],
], [6.4 * cm, 6.6 * cm, 3.5 * cm]))
E.append(P("Além desses, os `schema.yml` trazem dezenas de testes genéricos (unique, not_null, "
           "accepted_values, relationships, accepted_range, unique_combination_of_columns)."))
E.append(H2("CI e scripts"))
E.append(tabela([
    ["Arquivo", "Papel"],
    [".github/workflows/ci.yml", "Roda dbt deps + dbt build + source freshness a cada push/PR (após configurar secrets do GCP)"],
    ["scripts/load_to_bigquery.py", "Carrega os 5 Parquet do bucket para o dataset raw no BigQuery"],
    ["scripts/load_to_bigquery.sh", "Mesma ingestão usando o bq CLI"],
], [6.0 * cm, 10.5 * cm]))
E.append(PageBreak())

# ---------- 8. DECISOES ----------
E.append(H1("9. Decisões e achados (rastreabilidade do raciocínio)"))
E.append(P("Cada decisão de modelagem nasceu de um achado concreto na análise exploratória. "
           "Esta é a trilha do raciocínio, útil para novos insights."))
E.append(callout("Validação pelo dicionário oficial da fonte",
                 ["Depois de concluir a análise, localizei o `schema.yml` oficial publicado junto aos "
                  "dados (`gs://case_vagas/rmi/schema.yml`). Ele confirma, pela própria fonte, "
                  "decisões que eu havia tomado por inferência: o campo de frequência da avaliação é "
                  "o `campo original` de frequência do bimestre, enquanto a frequência da tabela "
                  "`frequencia` é um valor derivado (`100 - faltas_disciplina / dias_letivos`); "
                  "`disciplina_3` é oficialmente Língua Estrangeira (Inglês); o ano letivo original "
                  "é 2025 (anonimizado para 2000); e as notas receberam jitter de ±0,2. Ou seja, o "
                  "dicionário da fonte respalda o uso da frequência da avaliação como sinal de "
                  "absenteísmo."], bg=VERDE_BG, border=VERDE))
E.append(tabela([
    ["Achado nos dados", "Decisão tomada"],
    ["id_aluno é BYTES (hash)", "Converter para hexadecimal (to_hex) no staging"],
    ["turma não tem série/turno", "Tratar como matrícula; mart de turma usa o tamanho"],
    ["avaliacao é formato largo", "UNPIVOT no staging para formato longo"],
    ["Inglês (disciplina_3) 100% nula", "Documentar; intermediate ignora notas nulas"],
    ["Tabela frequencia sem variância (97-100%)", "NÃO usar para absenteísmo; manter como contraste"],
    ["Campo de frequência da avaliação varia 0-100%", "Usar como fonte do absenteísmo (sinal real: ~10% dos alunos)"],
    ["id_turma da frequencia com ~12% órfãos", "Join por id_aluno; relationship de turma como warn"],
    ["Duplicatas de grão", "Dedup com row_number() no staging"],
    ["bairro do aluno com ~0,07% nulos", "Teste customizado tolera até 1% (warn)"],
], [7.2 * cm, 9.3 * cm]))
E.append(callout("Insight central para explorar mais",
                 "A existência de duas frequências (uma sem sinal, outra com sinal) foi o achado que "
                 "mais mudou a entrega. Vale investigar também: desempenho por faixa etária, evolução "
                 "das notas entre bimestres, e se o tamanho da turma tem relação causal ou é artefato "
                 "da aleatorização.", bg=AMARELO_BG, border=colors.HexColor("#ca8a04")))
E.append(PageBreak())

# ---------- 9. NAO FEITO ----------
E.append(H1("10. O que NÃO foi feito e pendências"))
E.append(callout("Execução real no BigQuery: concluída",
                 ["O `dbt build` rodou de ponta a ponta no BigQuery Sandbox (projeto `exerciciodesafio`): "
                  "seed, 5 views de staging, 2 marts em tabela e 63 testes, com PASS=62, WARN=1 e ERROR=0. "
                  "O único WARN é o planejado (338.356 registros de frequência com turma órfã). "
                  "O `dbt source freshness` passou nas 5 fontes.",
                  "A execução real revelou dois ajustes que a simulação no DuckDB não pegou, ambos por "
                  "causa da tipagem estrita do BigQuery: (1) `accepted_values` em colunas numéricas "
                  "(`bimestre`, `ano_letivo`) precisou de `quote: false`, pois o dbt envolve os valores "
                  "em aspas e o BigQuery não compara INT64 com STRING; (2) o mart de absenteísmo não "
                  "pode ter `ORDER BY`, porque é uma tabela clusterizada por `bairro_id`.",
                  "Os números do mart no BigQuery conferem com a simulação: 10,41% de absenteísmo "
                  "crônico geral, 478 escolas com 20 ou mais alunos, média de 10,49% e faixa de 0% a 33,3%."],
                 bg=VERDE_BG, border=VERDE))
E.append(H2("Pendência remanescente"))
E.extend(BU([
    "CI no GitHub Actions: o workflow está pronto, mas só roda de fato depois de cadastrar os secrets "
    "`GCP_PROJECT` e `GCP_SA_KEY` (service account) no repositório.",
]))
E.append(H2("Itens deixados de fora de propósito"))
E.extend(BU([
    "Materialização incremental na frequencia (fica como table): proposto para produção por ser a maior tabela.",
    "Snapshots (SCD2) para histórico de aluno mudando de turma/escola.",
    "Data contracts (contract: enforced) nos marts.",
    "Hooks (pre/post-hook).",
    "Testes do dbt_expectations e uso do codegen (pacotes declarados, não explorados em testes).",
    "Cruzamento com a tabela pública de bairros (datario): os bairros estão em hash, não conciliam.",
]))
E.append(H2("Ressalvas de interpretação"))
E.extend(BU([
    "Os dados são anonimizados e aleatorizados: números servem para avaliar a técnica, não para conclusões reais sobre a rede.",
    "No absenteísmo, a frequência vem do campo de frequência da avaliação, mas a escola/região vem da tabela frequencia (única com escola e que concilia 100%). Essa junção está documentada.",
    "A escola do aluno foi definida por heurística (escola predominante), na ausência de um vínculo oficial.",
]))
E.append(PageBreak())

# ---------- ANEXO ----------
E.append(H1("Anexo: como os números foram verificados"))
E.append(P("Para garantir que as análises refletem a fonte, e não uma tabela gerada por mim:"))
E.extend(BU([
    "**Checksum:** o MD5 da cópia local de cada Parquet confere com o MD5 que o Google Cloud reporta para o objeto no bucket (mesmo hash e mesmo tamanho em bytes).",
    "**Leitura direta:** as estatísticas de frequência foram reproduzidas lendo o arquivo direto da URL do bucket (via httpfs do DuckDB), sem passar por cópia local, com resultado idêntico.",
    "**Simulação da lógica:** o pipeline de staging/intermediate/marts foi reproduzido em DuckDB para validar contagens e amostras (as deste documento) antes de rodar no BigQuery.",
    "**Execução real:** o `dbt build` no BigQuery reproduziu as mesmas contagens das tabelas brutas (97.044 alunos, 1.558 escolas, 221.687 avaliações, 2.727.684 registros de frequência) e os mesmos indicadores do mart de absenteísmo.",
]))
E.append(P("Resumo de contagens por model (linhas):", st_h3))
E.append(tabela([
    ["Model", "Linhas"],
    ["stg_educacao__alunos", f"{get_count('stg_alunos'):,}".replace(',', '.')],
    ["stg_educacao__escolas", f"{get_count('stg_escolas'):,}".replace(',', '.')],
    ["stg_educacao__matriculas", f"{get_count('stg_matriculas'):,}".replace(',', '.')],
    ["stg_educacao__frequencia", f"{get_count('stg_frequencia'):,}".replace(',', '.')],
    ["stg_educacao__avaliacoes", f"{get_count('stg_avaliacoes'):,}".replace(',', '.')],
    ["int_educacao__aluno_frequencia", f"{get_count('int_aluno_frequencia'):,}".replace(',', '.')],
    ["int_educacao__aluno_desempenho", f"{get_count('int_aluno_desempenho'):,}".replace(',', '.')],
    ["mart_educacao__absenteismo_regiao", f"{get_count('mart_absenteismo'):,}".replace(',', '.')],
    ["mart_educacao__desempenho_por_turma", f"{get_count('mart_desempenho_turma'):,}".replace(',', '.')],
], [9.5 * cm, 7.0 * cm]))
E.append(Spacer(1, 8))
E.append(P("Fim do documento de rastreio.", st_small))

# ----------------------------------------------------------------------------
def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CINZA)
    canvas.drawString(2 * cm, 1.2 * cm, "Desafio RMI  |  Documento de Rastreio")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, "Página %d" % doc.page)
    canvas.setStrokeColor(BORDA)
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.restoreState()

doc = BaseDocTemplate(SAIDA, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=2 * cm,
                      title="Desafio RMI - Rastreio", author="Matheus Bianco")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
doc.addPageTemplates([PageTemplate(id="base", frames=[frame], onPage=rodape)])
doc.build(E)
print("PDF gerado:", SAIDA)
