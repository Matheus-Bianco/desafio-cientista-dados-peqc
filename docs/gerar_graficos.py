# -*- coding: utf-8 -*-
"""Gera os graficos usados no PDF (salvos em docs/img)."""
import os
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "..", "data").replace("\\", "/")
IMG = os.path.join(AQUI, "img")
os.makedirs(IMG, exist_ok=True)
con = duckdb.connect()

AZUL = "#2563eb"
VERDE = "#16a34a"
CINZA = "#64748b"
VERMELHO = "#dc2626"

# 1) Distribuicao da frequencia (achado: nunca abaixo de 97%)
dist = con.execute(f"""
    SELECT round(frequencia, 1) AS faixa, count(*) AS n
    FROM read_parquet('{DATA}/frequencia')
    GROUP BY 1 ORDER BY 1
""").df()
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.bar(dist["faixa"].astype(str), dist["n"], color=AZUL)
ax.set_title("Distribuicao do percentual de frequencia (toda a rede)", fontsize=11, weight="bold")
ax.set_xlabel("Percentual de frequencia (%)")
ax.set_ylabel("Qtd. de registros")
ax.set_ylim(0, dist["n"].max() * 1.15)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
plt.xticks(rotation=45, fontsize=8)
ax.annotate("Nenhum registro abaixo de 97%:\na metrica de absenteismo < 75% fica zerada",
            xy=(0.02, 0.9), xycoords="axes fraction", fontsize=8.5, color="#b91c1c", weight="bold")
fig.text(0.01, 0.01, "Fonte: gs://case_vagas/rmi/frequencia (2,7M registros).", fontsize=7, color=CINZA)
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(IMG, "freq_distribuicao.png"), dpi=150)
plt.close()

# 2) Media de notas por faixa de tamanho de turma (insight real)
nota_tam = con.execute(f"""
with matricula as (
  select id_turma, count(*) n_mat from read_parquet('{DATA}/turma') group by id_turma
),
base as (
  select to_hex(id_aluno) aid, id_turma,
         disciplina_1 d1, disciplina_2 d2, disciplina_3 d3, disciplina_4 d4
  from read_parquet('{DATA}/avaliacao')
),
notas as (
  select id_turma, aid, d1 nota from base where d1 is not null
  union all select id_turma, aid, d2 from base where d2 is not null
  union all select id_turma, aid, d3 from base where d3 is not null
  union all select id_turma, aid, d4 from base where d4 is not null
),
media_aluno as (
  select id_turma, aid, avg(nota) mg from notas group by id_turma, aid
),
media_turma as (
  select id_turma, avg(mg) media_turma from media_aluno group by id_turma
),
j as (
  select m.n_mat, mt.media_turma,
    case when m.n_mat<=5 then '1. Ate 5'
         when m.n_mat<=10 then '2. 6 a 10'
         when m.n_mat<=20 then '3. 11 a 20'
         when m.n_mat<=30 then '4. 21 a 30'
         else '5. Mais de 30' end faixa
  from matricula m left join media_turma mt on m.id_turma = mt.id_turma
)
select faixa, round(avg(media_turma),2) media_notas, count(*) n_turmas
from j group by faixa order by faixa
""").df()
fig, ax = plt.subplots(figsize=(7.2, 3.4))
barras = ax.bar(nota_tam["faixa"], nota_tam["media_notas"], color=VERDE)
ax.set_title("Nota media por tamanho de turma", fontsize=11, weight="bold")
ax.set_xlabel("Faixa de tamanho da turma (alunos matriculados)")
ax.set_ylabel("Nota media (0 a 10)")
ax.set_ylim(0, 10)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
for b, v in zip(barras, nota_tam["media_notas"]):
    ax.text(b.get_x() + b.get_width()/2, v + 0.15, f"{v:.2f}", ha="center", fontsize=9, weight="bold")
fig.text(0.01, 0.01, "Fonte: tabelas avaliacao + turma (matricula). Notas 0-10.", fontsize=7, color=CINZA)
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(IMG, "nota_por_tamanho_turma.png"), dpi=150)
plt.close()

# 3) Distribuicao da frequencia COM SINAL (avaliacao.frequencia) por aluno
freq_aval = con.execute(f"""
with base as (
  select distinct to_hex(id_aluno) aid, id_turma, bimestre, frequencia fb
  from read_parquet('{DATA}/avaliacao')
  where frequencia is not null and not isnan(frequencia)
),
ma as (select aid, avg(fb) media from base group by aid)
select case
         when media < 50 then '<50'
         when media < 60 then '50-60'
         when media < 70 then '60-70'
         when media < 75 then '70-75'
         when media < 85 then '75-85'
         when media < 95 then '85-95'
         else '95-100' end faixa,
       count(*) n
from ma group by 1 order by 1
""").df()
ordem = ['<50', '50-60', '60-70', '70-75', '75-85', '85-95', '95-100']
freq_aval['faixa'] = freq_aval['faixa'].astype('category').cat.set_categories(ordem, ordered=True)
freq_aval = freq_aval.sort_values('faixa')
cores = [VERMELHO if f in ('<50', '50-60', '60-70', '70-75') else AZUL for f in freq_aval['faixa']]
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.bar(freq_aval['faixa'].astype(str), freq_aval['n'], color=cores)
ax.set_title("Frequencia media por aluno (fonte com sinal: avaliacao.frequencia)", fontsize=11, weight="bold")
ax.set_xlabel("Faixa de frequencia media (%)")
ax.set_ylabel("Qtd. de alunos")
ax.set_ylim(0, freq_aval['n'].max() * 1.15)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
ax.annotate("Em vermelho: abaixo de 75%\n(absenteismo cronico = 10,4% dos alunos)",
            xy=(0.30, 0.80), xycoords="axes fraction", fontsize=8.5, color=VERMELHO, weight="bold")
fig.text(0.01, 0.01, "Fonte: avaliacao.frequencia (media por aluno, 68.735 alunos com avaliacao).", fontsize=7, color=CINZA)
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(IMG, "freq_avaliacao_distribuicao.png"), dpi=150)
plt.close()

print("Graficos gerados em", IMG)
print(nota_tam.to_string(index=False))
