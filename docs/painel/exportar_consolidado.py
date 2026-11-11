# -*- coding: utf-8 -*-
"""
Consolida os marts do BigQuery (projeto exerciciodesafio) em uma base limpa para
o painel: um Excel multi-aba + CSVs por recorte. Apenas agregados, nunca dados crus.
"""
import os
from google.cloud import bigquery
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "dados")
os.makedirs(DADOS, exist_ok=True)

c = bigquery.Client(project="exerciciodesafio")
M = "exerciciodesafio.rmi_dev_marts"
S = "exerciciodesafio.rmi_dev_staging"  # staging (views)

def q(sql):
    return c.query(sql).result().to_dataframe()

# Desempenho por aluno (reproduz a logica do int_educacao__aluno_desempenho a
# partir da view de staging). Usado para as medias de REDE ponderadas por aluno:
# media das medias de turma subestima o valor real (turmas pequenas puxam para
# baixo), entao as medias de rede e por disciplina sao calculadas por aluno.
REDE = f"""
  select aluno_id, turma_id,
    round(avg(nota), 2)                                      as media_geral,
    round(avg(if(disciplina = 'Português',  nota, null)), 2) as media_portugues,
    round(avg(if(disciplina = 'Ciências',   nota, null)), 2) as media_ciencias,
    round(avg(if(disciplina = 'Matemática', nota, null)), 2) as media_matematica
  from `{S}.stg_educacao__avaliacoes`
  where nota is not null
  group by aluno_id, turma_id
"""

# 1. KPIs gerais (uma linha)
kpis = q(f"""
with abs as (
  select * from `{M}.mart_educacao__absenteismo_regiao` where n_alunos_com_frequencia >= 20
),
turma as (select * from `{M}.mart_educacao__desempenho_por_turma` where n_alunos_avaliados is not null),
rede as ({REDE})
select
  (select sum(n_alunos) from abs)                                               as alunos_avaliados,
  (select count(*) from abs)                                                    as escolas,
  (select count(*) from turma)                                                  as turmas,
  (select round(sum(n_alunos_absenteismo_cronico)/sum(n_alunos_com_frequencia)*100,1) from abs) as taxa_absenteismo_pct,
  (select round(avg(media_frequencia_regiao),1) from abs)                       as freq_media_avaliacao_pct,
  (select round(avg(media_frequencia_registros_regiao),1) from abs)            as freq_media_tabela_pct,
  -- media geral e aprovacao da REDE ponderadas por aluno (nao media de turmas)
  (select round(avg(media_geral),2) from rede)                                  as media_geral,
  (select round(avg(if(media_geral>=6,1,0))*100,1) from rede)                   as aprovacao_media_pct
""")

# 2. Absenteismo por faixa
faixa_abs = q(f"""
select case when taxa_absenteismo_cronico<0.05 then '< 5%'
 when taxa_absenteismo_cronico<0.10 then '5% a 10%'
 when taxa_absenteismo_cronico<0.15 then '10% a 15%'
 when taxa_absenteismo_cronico<0.20 then '15% a 20%'
 else '20% ou mais' end as faixa_absenteismo,
 count(*) as escolas
from `{M}.mart_educacao__absenteismo_regiao`
where n_alunos_com_frequencia>=20
group by 1
order by min(taxa_absenteismo_cronico)
""")

# 3. Desempenho x tamanho de turma
desemp_turma = q(f"""
select faixa_tamanho_turma,
 count(*) as turmas,
 round(avg(media_geral_turma),2) as media_geral,
 round(avg(taxa_aprovacao_media)*100,1) as aprovacao_pct
from `{M}.mart_educacao__desempenho_por_turma`
where n_alunos_avaliados is not null
group by 1 order by 1
""")

# 4. Media por disciplina (media da rede ponderada por aluno)
disc = q(f"""
with rede as ({REDE})
select 'Português' as disciplina, round(avg(media_portugues),2) as media from rede
union all select 'Ciências', round(avg(media_ciencias),2) from rede
union all select 'Matemática', round(avg(media_matematica),2) from rede
order by media desc
""")

# 5. Top 10 escolas com maior absenteismo (>=20 alunos)
top_escolas = q(f"""
select escola_id, bairro_id, n_alunos, n_alunos_absenteismo_cronico,
 round(taxa_absenteismo_cronico*100,1) as taxa_pct,
 round(media_frequencia_regiao,1) as freq_media_pct
from `{M}.mart_educacao__absenteismo_regiao`
where n_alunos_com_frequencia>=20
order by taxa_absenteismo_cronico desc, n_alunos desc
limit 10
""")

# 6. Contraste das duas frequencias
contraste = pd.DataFrame({
    "fonte": ["Tabela frequencia (por periodo)", "Frequencia da avaliacao (por bimestre)"],
    "frequencia_media_pct": [float(kpis.freq_media_tabela_pct[0]), float(kpis.freq_media_avaliacao_pct[0])],
    "tem_sinal": ["Nao (travada 97-100%)", "Sim (varia 0-100%)"],
})

tabelas = {
    "kpis": kpis,
    "absenteismo_por_faixa": faixa_abs,
    "desempenho_por_tamanho": desemp_turma,
    "media_por_disciplina": disc,
    "top10_escolas_absenteismo": top_escolas,
    "contraste_frequencias": contraste,
}

xlsx = os.path.join(DADOS, "RMI_consolidado_painel.xlsx")
with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
    for nome, df in tabelas.items():
        df.to_excel(w, sheet_name=nome[:31], index=False)
        df.to_csv(os.path.join(DADOS, f"{nome}.csv"), index=False, encoding="utf-8-sig")

print("OK. Arquivos em:", DADOS)
for nome, df in tabelas.items():
    print(f"  {nome}: {len(df)} linhas")
print("\n--- KPIs ---")
print(kpis.to_string(index=False))
