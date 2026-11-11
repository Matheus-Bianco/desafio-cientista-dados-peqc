# -*- coding: utf-8 -*-
"""
Exporta amostras legiveis das tabelas brutas (Parquet) para CSV e Excel,
para que seja possivel abrir e inspecionar os dados sem BigQuery/dbt.

- id_aluno e BYTES (hash); convertemos para STRING hexadecimal na exportacao.
- Geramos 200 linhas por tabela (amostra) + um Excel com todas as abas
  e uma aba de dicionario de dados.
"""
import os
import duckdb
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "..", "data")
OUT = os.path.join(AQUI, "amostras")
os.makedirs(OUT, exist_ok=True)

con = duckdb.connect()

def ler(nome, limite=200):
    return f"SELECT * FROM read_parquet('{os.path.join(DATA, nome)}') LIMIT {limite}"

# SELECTs amigaveis (hex no id_aluno) por tabela
consultas = {
    "aluno": """
        SELECT lower(to_hex(id_aluno)) AS id_aluno_hex, id_turma, faixa_etaria, bairro
        FROM read_parquet('{p}/aluno') LIMIT 200""",
    "escola": """
        SELECT id_escola, bairro FROM read_parquet('{p}/escola') LIMIT 200""",
    "turma": """
        SELECT ano, id_turma, lower(to_hex(id_aluno)) AS id_aluno_hex
        FROM read_parquet('{p}/turma') LIMIT 200""",
    "avaliacao": """
        SELECT lower(to_hex(id_aluno)) AS id_aluno_hex, id_turma, frequencia, bimestre,
               disciplina_1, disciplina_2, disciplina_3, disciplina_4
        FROM read_parquet('{p}/avaliacao') LIMIT 200""",
    "frequencia": """
        SELECT id_escola, lower(to_hex(id_aluno)) AS id_aluno_hex, id_turma,
               data_inicio, data_fim, disciplina, frequencia
        FROM read_parquet('{p}/frequencia') LIMIT 200""",
}

dfs = {}
for nome, sql in consultas.items():
    df = con.execute(sql.format(p=DATA.replace("\\", "/"))).df()
    dfs[nome] = df
    csv_path = os.path.join(OUT, f"{nome}_amostra.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[csv] {csv_path}  ({len(df)} linhas, {len(df.columns)} colunas)")

# Dicionario de dados (resumo tecnico de cada tabela)
dicionario = pd.DataFrame([
    ["aluno", "id_aluno", "BYTES (hash)", "Identificador unico do aluno. Exportado em hex."],
    ["aluno", "id_turma", "INT64", "Turma de matricula do aluno."],
    ["aluno", "faixa_etaria", "STRING", "Faixa etaria agrupada (0-5, 6-10, 11-14, 15-17, 18+)."],
    ["aluno", "bairro", "INT64", "Hash do bairro de residencia (contem nulos ~0,07%)."],
    ["escola", "id_escola", "INT64", "Identificador unico da escola."],
    ["escola", "bairro", "INT64", "Hash do bairro da escola."],
    ["turma", "ano", "INT64", "Ano letivo anonimizado para 2000."],
    ["turma", "id_turma", "INT64", "Identificador da turma."],
    ["turma", "id_aluno", "BYTES (hash)", "Aluno matriculado. Na pratica, 1 linha por aluno (matricula)."],
    ["avaliacao", "id_aluno", "BYTES (hash)", "Aluno avaliado."],
    ["avaliacao", "id_turma", "INT64", "Turma."],
    ["avaliacao", "frequencia", "FLOAT64", "Frequencia geral do bimestre (0-100). ~99% preenchida."],
    ["avaliacao", "bimestre", "STRING", "Bimestre de 1 a 4."],
    ["avaliacao", "disciplina_1", "FLOAT64", "Nota de Portugues (0-10)."],
    ["avaliacao", "disciplina_2", "FLOAT64", "Nota de Ciencias (0-10)."],
    ["avaliacao", "disciplina_3", "FLOAT64", "Nota de Ingles. 100% nula (achado)."],
    ["avaliacao", "disciplina_4", "FLOAT64", "Nota de Matematica (0-10)."],
    ["frequencia", "id_escola", "INT64", "Escola onde a frequencia foi apurada."],
    ["frequencia", "id_aluno", "BYTES (hash)", "Aluno."],
    ["frequencia", "id_turma", "INT64", "Turma. ~12% nao batem com a matricula (achado)."],
    ["frequencia", "data_inicio", "STRING", "Inicio do periodo (ano anonimizado 2000)."],
    ["frequencia", "data_fim", "STRING", "Fim do periodo (ano anonimizado 2000)."],
    ["frequencia", "disciplina", "STRING", "disciplina_1..4."],
    ["frequencia", "frequencia", "FLOAT64", "Percentual de frequencia (varia so entre 97% e 100%)."],
], columns=["tabela", "coluna", "tipo", "descricao"])

# Volumetria completa (todas as linhas, nao so a amostra)
vol = []
for nome in ["aluno", "escola", "turma", "avaliacao", "frequencia"]:
    n = con.execute(f"SELECT count(*) FROM read_parquet('{os.path.join(DATA, nome).replace(chr(92),'/')}')").fetchall()[0][0]
    vol.append([nome, n])
voldf = pd.DataFrame(vol, columns=["tabela", "total_de_linhas"])

xlsx = os.path.join(OUT, "RMI_tabelas_amostras.xlsx")
with pd.ExcelWriter(xlsx, engine="openpyxl") as xl:
    voldf.to_excel(xl, sheet_name="volumetria", index=False)
    dicionario.to_excel(xl, sheet_name="dicionario_de_dados", index=False)
    for nome, df in dfs.items():
        df.to_excel(xl, sheet_name=nome[:31], index=False)
print(f"[xlsx] {xlsx}")
print("Concluido.")
