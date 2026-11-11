# -*- coding: utf-8 -*-
"""
Gera o PDF didatico (101) do desafio RMI.

Monta um documento completo explicando o desafio, os dados, os conceitos
tecnicos (nivel iniciante) e a solucao construida em dbt + BigQuery.
"""
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, XPreformatted, KeepTogether,
)

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "img")
SAIDA = os.path.join(AQUI, "Desafio-RMI-Guia-101.pdf")

# ----------------------------------------------------------------------------
# Paleta e estilos
# ----------------------------------------------------------------------------
AZUL = colors.HexColor("#1e3a8a")
AZUL2 = colors.HexColor("#2563eb")
CINZA = colors.HexColor("#475569")
CINZA_CLARO = colors.HexColor("#f1f5f9")
VERDE = colors.HexColor("#16a34a")
AMARELO_BG = colors.HexColor("#fef9c3")
AZUL_BG = colors.HexColor("#eff6ff")
BORDA = colors.HexColor("#cbd5e1")

ss = getSampleStyleSheet()

st_title = ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold",
                          fontSize=26, textColor=AZUL, leading=30, alignment=TA_LEFT)
st_subtitle = ParagraphStyle("st", parent=ss["Normal"], fontSize=13, textColor=CINZA, leading=18)
st_h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                       fontSize=17, textColor=AZUL, spaceBefore=16, spaceAfter=8, leading=20)
st_h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                       fontSize=13, textColor=AZUL2, spaceBefore=12, spaceAfter=5, leading=16)
st_h3 = ParagraphStyle("h3", parent=ss["Heading3"], fontName="Helvetica-Bold",
                       fontSize=11, textColor=colors.HexColor("#0f172a"), spaceBefore=8, spaceAfter=3)
st_body = ParagraphStyle("b", parent=ss["Normal"], fontSize=10.3, leading=15.5,
                         alignment=TA_JUSTIFY, spaceAfter=6, textColor=colors.HexColor("#1e293b"))
st_bullet = ParagraphStyle("bu", parent=st_body, leftIndent=16, bulletIndent=4, spaceAfter=3)
st_code = ParagraphStyle("c", parent=ss["Code"], fontName="Courier", fontSize=8.3,
                         leading=11, textColor=colors.HexColor("#0f172a"))
st_small = ParagraphStyle("sm", parent=st_body, fontSize=8.5, textColor=CINZA, alignment=TA_LEFT)
st_th = ParagraphStyle("th", parent=st_body, fontName="Helvetica-Bold", fontSize=9.2,
                       textColor=colors.white, alignment=TA_LEFT, spaceAfter=0)
st_td = ParagraphStyle("td", parent=st_body, fontSize=9, leading=12, alignment=TA_LEFT, spaceAfter=0)
st_td_code = ParagraphStyle("tdc", parent=st_td, fontName="Courier", fontSize=8.5)
st_toc = ParagraphStyle("toc", parent=st_body, fontSize=10.5, leading=17, spaceAfter=1, alignment=TA_LEFT)
st_box_title = ParagraphStyle("bxt", parent=st_body, fontName="Helvetica-Bold", fontSize=10.3,
                              textColor=AZUL, spaceAfter=3)


def _prep(text):
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<font face="Courier" size="9">\1</font>', t)
    return t


def P(text, style=st_body):
    return Paragraph(_prep(text), style)


def H1(text):
    return Paragraph(_prep(text), st_h1)


def H2(text):
    return Paragraph(_prep(text), st_h2)


def H3(text):
    return Paragraph(_prep(text), st_h3)


def bullets(items, style=st_bullet):
    return [Paragraph(_prep(i), style, bulletText="\u2022") for i in items]


def code_block(text):
    safe = text.strip("\n").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    inner = XPreformatted(safe, st_code)
    tbl = Table([[inner]], colWidths=[16.0 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def callout(titulo, texto, bg=AZUL_BG, border=AZUL2):
    conteudo = [Paragraph(_prep(titulo), st_box_title)]
    if isinstance(texto, (list, tuple)):
        for t in texto:
            conteudo.append(Paragraph(_prep(t), st_body))
    else:
        conteudo.append(Paragraph(_prep(texto), st_body))
    tbl = Table([[conteudo]], colWidths=[16.0 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, border),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return tbl


def tabela(dados, larguras, header=True, font_header=st_th):
    linhas = []
    for r, row in enumerate(dados):
        linha = []
        for c, cell in enumerate(row):
            if r == 0 and header:
                linha.append(Paragraph(_prep(str(cell)), font_header))
            else:
                est = st_td_code if (isinstance(cell, str) and cell.startswith("`")) else st_td
                txt = cell[1:-1] if (isinstance(cell, str) and cell.startswith("`") and cell.endswith("`")) else cell
                linha.append(Paragraph(_prep(str(txt)), est))
        linhas.append(linha)
    tbl = Table(linhas, colWidths=larguras, repeatRows=1 if header else 0)
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
    ]
    if header:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
    tbl.setStyle(TableStyle(estilo))
    return tbl


# ----------------------------------------------------------------------------
# Numeracao de pagina + rodape
# ----------------------------------------------------------------------------
def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CINZA)
    canvas.drawString(2 * cm, 1.2 * cm, "Desafio Tecnico RMI  |  Guia 101")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, "Pagina %d" % doc.page)
    canvas.setStrokeColor(BORDA)
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.restoreState()


# ----------------------------------------------------------------------------
# Conteudo
# ----------------------------------------------------------------------------
E = []


def img(nome, largura=15.5 * cm):
    caminho = os.path.join(IMG, nome)
    from PIL import Image as PILImage
    with PILImage.open(caminho) as im:
        w, h = im.size
    altura = largura * h / w
    return Image(caminho, width=largura, height=altura)


# ---------- CAPA ----------
E.append(Spacer(1, 3.5 * cm))
E.append(Paragraph("Desafio Técnico de Cientista de Dados", st_subtitle))
E.append(Spacer(1, 0.3 * cm))
E.append(Paragraph("Registro Municipal Integrado (RMI)", st_title))
E.append(Spacer(1, 0.4 * cm))
E.append(Paragraph("Guia completo (101): do enunciado à solução em dbt e BigQuery, "
                   "com explicação de cada conceito técnico do zero.", st_subtitle))
E.append(Spacer(1, 1.2 * cm))
E.append(tabela([
    ["Autor", "Matheus Bianco"],
    ["Stack", "dbt-core + dbt-bigquery, Python, DuckDB, SQL"],
    ["Fonte dos dados", "gs://case_vagas/rmi (Google Cloud Storage, público)"],
    ["Projeto", "desafio-rmi-ds"],
], larguras=[4 * cm, 12 * cm], header=False))
E.append(Spacer(1, 0.8 * cm))
E.append(callout("Para quem é este documento",
                 "Foi escrito para quem está começando em dados. Cada termo técnico "
                 "(fork, dbt, warehouse, staging, teste de dados) é explicado em linguagem "
                 "simples na primeira vez que aparece. Se você já é experiente, pode pular "
                 "direto para as seções 6 e 7."))
E.append(PageBreak())

# ---------- SUMARIO ----------
E.append(H1("Sumário"))
sumario = [
    "1. Introdução: o que é este desafio",
    "2. Glossário essencial (os conceitos do zero)",
    "3. O que o desafio pedia, parte por parte",
    "4. Os insumos: de onde vieram os dados e quais são as tabelas",
    "5. Análise exploratória: o que descobrimos nos dados",
    "6. A solução: o que foi feito e como, detalhe por detalhe",
    "7. Estratégia de testes de qualidade",
    "8. Resultados e análise de negócio",
    "9. Como reproduzir o projeto do zero",
    "10. Trade-offs e próximos passos",
    "Anexo A: arquivos entregues",
]
for s in sumario:
    E.append(Paragraph(_prep(s), st_toc))
E.append(PageBreak())

# ---------- 1. INTRODUCAO ----------
E.append(H1("1. Introdução: o que é este desafio"))
E.append(P("Este desafio é um teste técnico para a vaga de **Cientista de Dados** "
           "em um contexto de setor público: o **Registro Municipal Integrado (RMI)**, "
           "descrito como o grande repositório de dados da Prefeitura do Rio de Janeiro, "
           "que reúne informações de saúde, educação, assistência social e outros sistemas."))
E.append(P("O objetivo não é criar um modelo de machine learning. É demonstrar uma "
           "habilidade que está no coração do trabalho de dados moderno: a **engenharia de "
           "analytics**, ou seja, pegar dados brutos e bagunçados e transformá-los em tabelas "
           "limpas, testadas, documentadas e confiáveis, prontas para alimentar relatórios e "
           "decisões. Pense nisso como a diferença entre ingredientes crus e um prato pronto "
           "para servir."))
E.append(P("Para isso, o desafio pede o uso de uma ferramenta chamada **dbt** sobre um banco "
           "de dados analítico chamado **BigQuery**, usando dados educacionais reais "
           "(anonimizados) da rede municipal."))
E.append(callout("A frase mais importante do enunciado",
                 "\"Profundidade importa mais que completude. Melhor ter menos models com testes "
                 "excelentes e documentação clara do que muitos models superficiais.\" "
                 "Toda a solução foi construída com esse princípio em mente.",
                 bg=AMARELO_BG, border=colors.HexColor("#ca8a04")))

# ---------- 2. GLOSSARIO ----------
E.append(H1("2. Glossário essencial (os conceitos do zero)"))
E.append(P("Antes de entrar na solução, vamos definir cada termo que aparece no desafio. "
           "Não pule esta seção: ela é a base para entender todo o resto."))

glossario = [
    ("Dado bruto (raw)", "O dado como ele chega da fonte, sem nenhum tratamento. Costuma ter "
     "erros, duplicatas, nomes ruins e formatos estranhos."),
    ("Data warehouse (armazém de dados)", "Um banco de dados feito para análise (não para o "
     "dia a dia de um sistema). Guarda grandes volumes e responde perguntas analíticas rápido. "
     "Aqui o warehouse é o BigQuery."),
    ("BigQuery", "O data warehouse do Google, na nuvem. Você envia tabelas para lá e faz "
     "consultas em SQL sobre milhões de linhas em segundos, sem gerenciar servidores."),
    ("GCS (Google Cloud Storage) / bucket", "Um serviço de armazenamento de arquivos na nuvem "
     "do Google. Um 'bucket' é como uma pasta gigante na internet. Os dados do desafio estão "
     "em um bucket público chamado case_vagas."),
    ("Parquet", "Um formato de arquivo para dados em tabela, otimizado para análise. Diferente "
     "de um CSV, ele guarda os dados por coluna e já sabe o tipo de cada campo, o que o torna "
     "muito mais rápido e leve."),
    ("SQL", "A linguagem usada para consultar e transformar dados em bancos. Comandos como "
     "SELECT, WHERE, JOIN e GROUP BY são SQL."),
    ("dbt (data build tool)", "A ferramenta central do desafio. Com ela, você escreve as "
     "transformações dos dados em arquivos SQL organizados, e o dbt cuida de rodar tudo na "
     "ordem certa, testar e documentar. É como um 'framework' para organizar o SQL de um "
     "projeto de dados de forma profissional."),
    ("Model (model do dbt)", "Cada arquivo .sql no dbt é um 'model'. Ele contém um SELECT que "
     "define uma nova tabela ou view. Um model pode usar outro como fonte."),
    ("Source (fonte)", "A declaração, no dbt, de onde estão os dados brutos (as tabelas que "
     "você carregou no warehouse). É o ponto de partida do fluxo."),
    ("View x Table", "Uma 'table' (tabela) guarda os dados fisicamente. Uma 'view' é só uma "
     "consulta salva que roda na hora em que é usada (não ocupa espaço com dados). O dbt "
     "chama a escolha entre elas de 'materialização'."),
    ("Materialização", "Como o dbt grava o resultado de um model: como view, table, ephemeral "
     "(só uma consulta reaproveitada, sem criar objeto) ou incremental (atualiza só o que mudou)."),
    ("Camadas: staging, intermediate, marts", "Uma organização em níveis. Staging limpa cada "
     "tabela bruta. Intermediate combina tabelas e aplica regras de negócio. Marts entrega a "
     "tabela final que responde a uma pergunta. É uma linha de montagem."),
    ("Teste de dados", "Uma verificação automática da qualidade. Ex: 'a coluna id nunca pode "
     "ser nula' ou 'a nota tem que estar entre 0 e 10'. Se a regra falhar, o teste acusa."),
    ("Lineage (linhagem)", "O mapa que mostra de onde cada tabela veio e para onde vai. Ajuda "
     "a entender dependências e o impacto de uma mudança."),
    ("Git e repositório", "Git é o sistema que controla versões do código (guarda o histórico "
     "de mudanças). Um 'repositório' (ou repo) é a pasta do projeto versionada por ele, "
     "normalmente hospedada em sites como GitHub."),
    ("Fork", "Fazer um 'fork' é criar uma cópia sua de um repositório de outra pessoa, na sua "
     "própria conta. Você trabalha na sua cópia sem mexer no original. O desafio pede um fork "
     "para você colocar sua solução."),
    ("Commit e Pull Request (PR)", "Um 'commit' é um ponto salvo no histórico do Git, com uma "
     "mensagem do que mudou. Um 'Pull Request' é um pedido para juntar suas mudanças ao projeto "
     "principal, normalmente revisado por outra pessoa."),
    ("CI (Integração Contínua)", "Um robô que roda testes automaticamente toda vez que você "
     "envia código, garantindo que nada quebrou. Aqui usamos o GitHub Actions para rodar o dbt."),
    ("Anonimização", "Processo de remover ou embaralhar dados pessoais (nomes, CPF, endereço) "
     "para proteger a privacidade. Nos dados do desafio, IDs viraram códigos sintéticos e "
     "números foram aleatorizados."),
    ("Hash", "Uma função que transforma um valor em um código de tamanho fixo, de um jeito que "
     "não dá para voltar ao original. Usado aqui para anonimizar IDs e bairros."),
    ("Grão (granularidade)", "O que uma linha da tabela representa. Ex: 'uma linha por aluno' "
     "ou 'uma linha por aluno/dia'. Definir o grão certo evita contagens erradas."),
]
for termo, desc in glossario:
    E.append(Paragraph(_prep("**" + termo + ":** " + desc), st_bullet, bulletText="\u2022"))
E.append(PageBreak())

# ---------- 3. O QUE O DESAFIO PEDIA ----------
E.append(H1("3. O que o desafio pedia, parte por parte"))
E.append(P("O enunciado divide o trabalho em três partes. Abaixo, cada uma em linguagem simples."))

E.append(H2("Parte 1: Projeto dbt e Modelagem"))
E.append(P("Construir um projeto dbt do zero que pegue os dados brutos e os organize em "
           "camadas. Em detalhe, pedia:"))
for it in bullets([
    "Configurar o projeto com as 'sources' apontando para os dados e uma estrutura de pastas organizada.",
    "Criar a camada de **staging** para pelo menos 4 tabelas, com limpeza, padronização de nomes, tipagem e tratamento de nulos.",
    "Criar pelo menos 1 model **intermediate** que combine várias fontes (ex: alunos + matrículas + frequência).",
    "Construir pelo menos 1 **mart** que responda a uma pergunta real de gestores públicos.",
]):
    E.append(it)

E.append(H2("Parte 2: Testes e Qualidade de Dados (a mais importante)"))
E.append(P("O enunciado diz explicitamente que esta é a parte mais importante. Pedia:"))
for it in bullets([
    "Aplicar testes genéricos prontos do dbt (unique, not_null, accepted_values, relationships), com critério: testar o que importa, e explicar por quê.",
    "Criar pelo menos 2 testes customizados de **regra de negócio** (ex: nenhuma frequência pode ter data anterior à matrícula).",
]):
    E.append(it)

E.append(H2("Parte 3: Documentação e Análise"))
for it in bullets([
    "Produzir documentação (README) que permita a um novo membro entender e manter o projeto: setup, lineage, decisões de arquitetura e trade-offs.",
    "Opcionalmente (diferencial), um notebook de análise exploratória em Python.",
]):
    E.append(it)

E.append(H2("Diferenciais sugeridos"))
E.append(P("Uso de pacotes dbt (dbt_utils, dbt_expectations, codegen), configuração de "
           "'freshness' nas sources, uso de tags e exposures, data contracts, análise "
           "exploratória e CI com GitHub Actions. **Todos foram implementados nesta solução.**"))

E.append(H2("Como o desafio é avaliado"))
E.append(tabela([
    ["Critério", "O que observam"],
    ["Modelagem e arquitetura dbt", "Organização das camadas, nomes, materializações."],
    ["Estratégia de testes e qualidade", "Cobertura intencional e testes de regra de negócio."],
    ["SQL e lógica analítica", "Clareza e correção das transformações."],
    ["Documentação e comunicação", "README, lineage e explicação das decisões."],
], larguras=[6 * cm, 10 * cm]))
E.append(PageBreak())

# ---------- 4. INSUMOS ----------
E.append(H1("4. Os insumos: de onde vieram os dados e quais são as tabelas"))
E.append(H2("De onde foram baixados"))
E.append(P("Os dados estão em um **bucket público do Google Cloud Storage**. O enunciado "
           "aponta o endereço do console:"))
E.append(code_block("https://console.cloud.google.com/storage/browser/case_vagas/rmi"))
E.append(P("Investigando o bucket, descobri dois detalhes práticos importantes:"))
for it in bullets([
    "Os arquivos foram salvos **sem a extensão .parquet** (o objeto se chama apenas 'aluno', 'escola', etc.), então baixar por 'aluno.parquet' dá erro 404.",
    "O bucket também contém um arquivo **schema.yml** com a descrição oficial das colunas, o que ajudou a confirmar tipos e significados.",
]):
    E.append(it)
E.append(P("O download direto de cada tabela pode ser feito por URL pública, por exemplo:"))
E.append(code_block("https://storage.googleapis.com/case_vagas/rmi/aluno\n"
                     "https://storage.googleapis.com/case_vagas/rmi/escola\n"
                     "https://storage.googleapis.com/case_vagas/rmi/turma\n"
                     "https://storage.googleapis.com/case_vagas/rmi/avaliacao\n"
                     "https://storage.googleapis.com/case_vagas/rmi/frequencia"))
E.append(callout("Tabelas disponibilizadas para você ver",
                 ["Exportei amostras legíveis das 5 tabelas (200 linhas cada) para a pasta "
                  "`docs/amostras/`, em dois formatos:",
                  "1) Um arquivo por tabela em CSV (ex: `aluno_amostra.csv`).",
                  "2) Um único Excel, `RMI_tabelas_amostras.xlsx`, com uma aba por tabela, "
                  "mais uma aba de volumetria e uma de dicionário de dados.",
                  "Nessas amostras, o id_aluno (que no original é um código binário) aparece "
                  "convertido para texto hexadecimal, para ficar legível."]))

E.append(H2("As cinco tabelas e a auxiliar"))
E.append(tabela([
    ["Tabela", "O que representa", "Grão (uma linha é...)", "Linhas"],
    ["aluno", "Cadastro de alunos", "um aluno", "97.044"],
    ["escola", "Cadastro de escolas", "uma escola", "1.558"],
    ["turma", "Na prática, a matrícula aluno-turma", "um aluno/turma", "97.044"],
    ["avaliacao", "Notas por bimestre (formato largo)", "um aluno/turma/bimestre", "221.687"],
    ["frequencia", "Frequência por período e disciplina", "aluno/turma/escola/período/disciplina", "2.727.684"],
], larguras=[2.6 * cm, 5.1 * cm, 5.3 * cm, 2.6 * cm]))
E.append(Spacer(1, 4))
E.append(P("Há ainda uma tabela auxiliar pública no BigQuery, "
           "`datario.dados_mestres.bairro`, com o cadastro de bairros do Rio. Como os bairros "
           "nos dados estão em hash (não dá para cruzar diretamente), ela não foi necessária "
           "para os marts construídos."))

E.append(H2("Dicionário de dados (colunas principais)"))
E.append(tabela([
    ["Tabela.coluna", "Tipo", "Descrição"],
    ["aluno.id_aluno", "BYTES", "ID do aluno (código binário; vira hexadecimal no projeto)."],
    ["aluno.id_turma", "INT64", "Turma de matrícula."],
    ["aluno.faixa_etaria", "STRING", "0-5, 6-10, 11-14, 15-17, 18+."],
    ["aluno.bairro", "INT64", "Hash do bairro (tem alguns nulos)."],
    ["escola.id_escola", "INT64", "ID da escola."],
    ["escola.bairro", "INT64", "Hash do bairro da escola."],
    ["turma.ano", "INT64", "Ano letivo anonimizado para 2000."],
    ["turma.id_turma / id_aluno", "INT64 / BYTES", "Liga aluno à turma (matrícula)."],
    ["avaliacao.bimestre", "STRING", "1 a 4."],
    ["avaliacao.disciplina_1..4", "FLOAT64", "Notas: Português, Ciências, Inglês, Matemática."],
    ["avaliacao.frequencia", "FLOAT64", "Frequência do bimestre (0-100; ~99% preenchida)."],
    ["frequencia.data_inicio/fim", "STRING", "Período de apuração (ano 2000)."],
    ["frequencia.disciplina", "STRING", "disciplina_1..4."],
    ["frequencia.frequencia", "FLOAT64", "Percentual de presença (0 a 100)."],
], larguras=[4.3 * cm, 2.6 * cm, 9.1 * cm]))
E.append(PageBreak())

# ---------- 5. EDA ----------
E.append(H1("5. Análise exploratória: o que descobrimos nos dados"))
E.append(P("Antes de modelar, baixei as tabelas e investiguei com uma ferramenta chamada "
           "**DuckDB** (um banco analítico que roda no próprio computador, ótimo para explorar "
           "arquivos Parquet rapidamente). Essa etapa, a **análise exploratória de dados (EDA)**, "
           "revelou vários problemas de qualidade que guiaram todas as decisões seguintes. "
           "Entender os dados antes de transformá-los é o que separa um trabalho amador de um "
           "profissional."))

achados = [
    ("1. O ID do aluno é binário, não texto", "O campo id_aluno vem como BYTES (um hash de 17 "
     "bytes), e não como texto. Se usado cru, fica ilegível. **Decisão:** converter para texto "
     "hexadecimal logo no staging, criando uma chave estável e legível."),
    ("2. A tabela 'turma' é, na verdade, matrícula", "Apesar do nome e da descrição do enunciado "
     "(que fala em série e turno), a tabela só tem ano, id_turma e id_aluno, com uma linha por "
     "aluno. **Decisão:** tratá-la como tabela de matrículas e não inventar colunas que não existem."),
    ("3. A tabela de avaliação está em formato 'largo'", "Cada disciplina é uma coluna "
     "(disciplina_1 a 4), em vez de uma linha por disciplina. **Decisão:** 'girar' a tabela para "
     "o formato 'longo' (uma linha por aluno/bimestre/disciplina) usando UNPIVOT."),
    ("4. A disciplina de Inglês está 100% vazia", "Na avaliação, a coluna disciplina_3 (Inglês) "
     "não tem nenhuma nota preenchida: zero de 221.687. **Decisão:** manter a estrutura e um "
     "teste que torna essa ausência visível, em vez de escondê-la."),
    ("5. Existem duas frequências, e só uma tem sinal", "A tabela `frequencia` (por período) fica "
     "sempre entre 97% e 100%, sem variação, então mediria absenteísmo zero. Mas há um segundo "
     "campo, `avaliacao.frequencia` (frequência geral por bimestre), que varia de 0 a 100% "
     "(média 89%). **Decisão:** medir o absenteísmo pela `avaliacao.frequencia`, que é a fonte "
     "com sinal real, e manter a outra apenas como contraste. Esse foi o achado que mais "
     "influenciou a análise."),
    ("6. Chaves que não conciliam", "Cerca de 12% das linhas de frequência apontam para uma "
     "turma que não existe na matrícula. Já o id_aluno bate 100% entre todas as tabelas. "
     "**Decisão:** fazer os cruzamentos pelo id_aluno (confiável) e tratar a relação por turma "
     "como apenas um aviso, não um erro que quebra o pipeline."),
    ("7. Linhas duplicadas", "Há cerca de 2.600 duplicatas exatas na frequência e 34 na "
     "avaliação. **Decisão:** remover duplicatas no staging com uma técnica de numeração de "
     "linhas (row_number)."),
]
for t, d in achados:
    E.append(H3(t))
    E.append(P(d))

E.append(KeepTogether([H2("A fonte óbvia (tabela frequencia) não varia"), img("freq_distribuicao.png")]))
E.append(PageBreak())

# ---------- 6. A SOLUCAO ----------
E.append(H1("6. A solução: o que foi feito e como, detalhe por detalhe"))
E.append(P("A solução é um projeto dbt chamado `desafio-rmi-ds`, organizado nas três camadas "
           "clássicas. O diagrama abaixo mostra o 'lineage', o caminho que os dados percorrem "
           "da esquerda (bruto) para a direita (pronto para análise)."))

E.append(H2("Mapa do projeto (lineage)"))
E.append(tabela([
    ["Fontes (BigQuery raw)", "Staging (views)", "Intermediate", "Marts (tables)"],
    ["aluno", "stg...__alunos", "int...__aluno_frequencia", "mart...__absenteismo_regiao"],
    ["escola", "stg...__escolas", "int...__aluno_desempenho", "mart...__desempenho_por_turma"],
    ["turma", "stg...__matriculas", "", ""],
    ["avaliacao", "stg...__avaliacoes", "", ""],
    ["frequencia", "stg...__frequencia", "", ""],
], larguras=[3.4 * cm, 4.2 * cm, 4.6 * cm, 4.6 * cm]))
E.append(Spacer(1, 4))
E.append(P("A regra de nomes segue o padrão `camada_dominio__entidade`. O domínio aqui é "
           "'educacao'. Assim, quando o projeto crescer para saúde ou assistência social, os "
           "nomes continuam organizados."))

E.append(H2("Passo 0: trazer os dados para o BigQuery (ingestão)"))
E.append(P("Antes do dbt, os Parquet precisam estar no warehouse. Escrevi um script Python "
           "(`scripts/load_to_bigquery.py`) que carrega cada arquivo direto do bucket para um "
           "conjunto de dados 'raw' no BigQuery. O próprio BigQuery lê arquivos Parquet "
           "direto do GCS, então nem é preciso baixar no computador."))

E.append(H2("Camada 1: Staging (limpar cada tabela)"))
E.append(P("Cada tabela bruta ganha um model de staging (materializado como **view**, porque é "
           "leve e sempre reflete a fonte). O que cada um faz:"))
for it in bullets([
    "**stg_educacao__alunos:** converte o id_aluno de binário para hexadecimal, renomeia e padroniza a faixa etária.",
    "**stg_educacao__escolas:** padroniza os nomes das colunas de escola.",
    "**stg_educacao__matriculas:** renomeia a tabela 'turma' para o que ela realmente é (matrícula).",
    "**stg_educacao__frequencia:** converte datas de texto para data de verdade, traduz os códigos de disciplina (disciplina_1 vira 'Português') e remove duplicatas.",
    "**stg_educacao__avaliacoes:** gira o formato largo para longo (UNPIVOT) e remove duplicatas.",
]):
    E.append(it)
E.append(P("Exemplo real do staging de alunos, com a conversão do ID e a padronização:"))
E.append(code_block(
    "select\n"
    "    to_hex(id_aluno)                 as aluno_id,   -- binario -> hexadecimal\n"
    "    id_turma                         as turma_id,\n"
    "    nullif(trim(faixa_etaria), '')   as faixa_etaria,\n"
    "    bairro                           as bairro_id\n"
    "from {{ source('rmi_educacao', 'aluno') }}"))
E.append(P("O trecho `{{ source(...) }}` é a forma do dbt de dizer 'leia a tabela bruta "
           "chamada aluno'. Isso cria automaticamente o lineage."))

E.append(H2("Camada 2: Intermediate (combinar e aplicar regras)"))
E.append(P("Aqui as tabelas limpas se juntam e nascem as métricas. São materializados como "
           "**ephemeral** (viram apenas um trecho de consulta reaproveitado, sem criar tabela "
           "física), o que mantém o warehouse limpo."))
for it in bullets([
    "**int_educacao__aluno_frequencia:** junta aluno + frequência pelo id_aluno (a chave confiável) e calcula, por aluno, a frequência média, mínima e máxima, além de marcar quem tem absenteísmo crônico. A escola do aluno é definida pela 'escola predominante' (onde ele tem mais registros).",
    "**int_educacao__aluno_desempenho:** a partir das notas, calcula a média geral do aluno e a média por disciplina.",
]):
    E.append(it)

E.append(H2("Camada 3: Marts (responder perguntas de negócio)"))
E.append(P("São as tabelas finais, materializadas como **table** para consulta rápida em "
           "dashboards. Cada uma responde a uma pergunta de gestor:"))
for it in bullets([
    "**mart_educacao__absenteismo_regiao:** por escola e região, qual a taxa de alunos com frequência média abaixo de 75%? (Resposta nos dados: zero, pelo achado 5. O mart também expõe a distribuição, para funcionar quando houver dados reais.)",
    "**mart_educacao__desempenho_por_turma:** como o tamanho da turma se relaciona com o desempenho médio? (O enunciado sugeria série/turno, que não existem; adaptei para o tamanho da turma, que dá para calcular.)",
]):
    E.append(it)

E.append(H2("Peças de apoio"))
for it in bullets([
    "**Seed:** uma pequena tabela de apoio (CSV) com o de/para dos códigos de disciplina.",
    "**Macro:** um pedaço de SQL reutilizável (nome_disciplina) que traduz os códigos, evitando repetição.",
    "**Exposure:** uma declaração de que um painel consome os marts, para rastrear o impacto de mudanças.",
    "**Pacotes:** dbt_utils, dbt_expectations e codegen, bibliotecas prontas da comunidade.",
]):
    E.append(it)
E.append(PageBreak())

# ---------- 7. TESTES ----------
E.append(H1("7. Estratégia de testes de qualidade"))
E.append(P("Esta é a parte mais valorizada. A ideia é simples: um teste é uma afirmação sobre "
           "os dados que o dbt verifica sozinho. Se a afirmação for falsa, o teste falha e avisa. "
           "Isso impede que dados errados cheguem aos relatórios. A cobertura foi **intencional**: "
           "cada teste responde a uma pergunta de confiabilidade."))

E.append(H2("Testes genéricos (prontos)"))
E.append(tabela([
    ["Teste", "O que garante", "Exemplo de uso"],
    ["unique", "Não há valores repetidos", "aluno_id na dimensão de alunos"],
    ["not_null", "Não há valores vazios", "chaves e colunas obrigatórias"],
    ["accepted_values", "Só valores de uma lista", "bimestre só pode ser 1,2,3,4"],
    ["relationships", "Toda chave existe na outra tabela", "aluno da frequência existe em alunos"],
    ["accepted_range", "Valor dentro de um intervalo", "nota entre 0 e 10; frequência 0 a 100"],
], larguras=[3.2 * cm, 6.3 * cm, 6.5 * cm]))
E.append(Spacer(1, 4))
E.append(P("Um detalhe de critério: a relação da frequência com a matrícula pela turma foi "
           "marcada como **apenas aviso** (warn), de propósito, porque sabemos que 12% não "
           "conciliam. Em vez de deixar o pipeline quebrar por um problema conhecido da origem, "
           "o teste registra o aviso e seguimos cruzando pelo id_aluno."))

E.append(H2("Teste genérico customizado"))
E.append(P("Criei um teste próprio, `proporcao_nulos_abaixo_de`, que permite uma fração "
           "conhecida de nulos e só avisa quando a qualidade piora. Diferente do not_null (que "
           "exige zero nulos), ele monitora o bairro do aluno, que tem ~0,07% de nulos, sem "
           "travar o projeto."))

E.append(H2("Testes de regra de negócio (singular)"))
E.append(P("Além dos genéricos, escrevi testes em SQL que validam regras do mundo da educação. "
           "Cada um retorna linhas apenas quando a regra é violada (ou seja, passar é não "
           "retornar nada):"))
for it in bullets([
    "**Datas coerentes:** nenhum período de frequência pode começar depois de terminar (data_inicio > data_fim).",
    "**Grão sem duplicatas:** depois da limpeza, cada combinação aluno/turma/escola/período/disciplina na frequência deve ser única.",
    "**Nota exige matrícula:** nenhum aluno pode ter nota lançada sem possuir matrícula correspondente.",
]):
    E.append(it)
E.append(callout("Por que isso importa",
                 "Testes de regra de negócio são o que diferencia 'dados que existem' de "
                 "'dados em que dá para confiar'. Eles codificam o conhecimento do domínio "
                 "(educação) dentro do pipeline, de forma que qualquer carga futura seja "
                 "verificada automaticamente."))
E.append(PageBreak())

# ---------- 8. RESULTADOS ----------
E.append(H1("8. Resultados e análise de negócio"))
E.append(H2("Absenteísmo por região"))
E.append(P("A fonte óbvia para absenteísmo seria a tabela `frequencia`, mas ela não tem "
           "variação (achado 5), o que daria taxa zero em toda a rede. Ao explorar os dados, "
           "encontrei o sinal em outro campo, a `avaliacao.frequencia` (frequência geral por "
           "bimestre), e construí o mart sobre ela. O resultado passa a ser acionável: cerca de "
           "**10,4% dos alunos** têm frequência média abaixo de 75%, e a taxa varia de **0% a "
           "33% entre as escolas** (478 escolas com 20 ou mais alunos, média de 10,5%). Escolher "
           "a fonte certa, e documentar por que a tabela `frequencia` foi descartada, é o "
           "coração do raciocínio analítico que o desafio pede."))
E.append(img("freq_avaliacao_distribuicao.png"))

E.append(H2("Desempenho por tamanho de turma"))
E.append(P("Aqui aparece um sinal real e interessante: turmas maiores têm nota média mais alta. "
           "Turmas de até 5 alunos têm média ~4,1, enquanto turmas com mais de 30 alunos têm "
           "média ~6,1. Vale lembrar que, por serem dados aleatorizados, isso não deve ser "
           "lido como conclusão pedagógica real; provavelmente reflete como as notas foram "
           "distribuídas. O importante é que o pipeline consegue cruzar tamanho de turma com "
           "desempenho de ponta a ponta."))
E.append(KeepTogether([img("nota_por_tamanho_turma.png")]))
E.append(PageBreak())

# ---------- 9. COMO REPRODUZIR ----------
E.append(H1("9. Como reproduzir o projeto do zero"))
E.append(P("Passo a passo, assumindo que você nunca rodou dbt. Você vai precisar de Python, "
           "uma conta Google (o BigQuery tem um modo gratuito, o 'Sandbox') e o utilitário "
           "gcloud para autenticar."))
E.append(H3("1) Preparar o ambiente Python"))
E.append(code_block("python -m venv .venv\n"
                     ".venv\\Scripts\\activate          # Windows\n"
                     "pip install -r requirements.txt"))
E.append(H3("2) Autenticar no Google Cloud"))
E.append(code_block("gcloud auth application-default login\n"
                     "$env:GCP_PROJECT = \"seu-projeto-sandbox\"   # PowerShell"))
E.append(H3("3) Carregar os dados do bucket para o BigQuery"))
E.append(code_block("python scripts/load_to_bigquery.py --dataset rmi_raw --location US"))
E.append(H3("4) Configurar o acesso do dbt e rodar"))
E.append(code_block("copy profiles.yml.example %USERPROFILE%\\.dbt\\profiles.yml\n"
                     "dbt deps        # baixa os pacotes\n"
                     "dbt build       # cria e TESTA tudo de uma vez\n"
                     "dbt docs generate && dbt docs serve   # documentacao visual com o lineage"))
E.append(callout("Dica para iniciantes",
                 "O comando `dbt build` faz tudo em sequência e na ordem certa: cria as views e "
                 "tabelas (dbt run), carrega os seeds e roda todos os testes (dbt test). Se algo "
                 "estiver errado nos dados, ele para e te mostra qual teste falhou."))

E.append(H1("10. Trade-offs e próximos passos"))
E.append(P("Nenhuma solução é perfeita. Decisões que tomei e o que faria com mais tempo:"))
for it in bullets([
    "Usei intermediate como ephemeral (warehouse limpo), abrindo mão de inspecionar a tabela intermediária isoladamente.",
    "A escola do aluno foi definida por heurística (escola predominante), já que os dados não trazem um vínculo oficial.",
    "Com mais tempo: materializar a frequência como incremental e particionada por mês (é a maior tabela, 2,7M linhas), adicionar data contracts, snapshots para histórico e mais testes de distribuição.",
    "Investigar com a equipe de origem por que 12% das turmas da frequência não batem com a matrícula.",
]):
    E.append(it)

# ---------- ANEXO ----------
E.append(H1("Anexo A: arquivos entregues"))
E.append(tabela([
    ["Arquivo / pasta", "O que é"],
    ["desafio-rmi-ds/", "O projeto dbt completo."],
    ["README.md", "Documentação técnica para manutenção."],
    ["models/staging, intermediate, marts", "Os models SQL em cada camada."],
    ["tests/", "Os testes de regra de negócio."],
    ["macros/", "Macro de disciplina e teste customizado."],
    ["seeds/", "Tabela de apoio (de/para de disciplina)."],
    ["scripts/", "Ingestão dos dados para o BigQuery."],
    ["notebooks/eda.ipynb", "Análise exploratória em Python."],
    [".github/workflows/ci.yml", "Robô de testes (CI)."],
    ["docs/amostras/", "Amostras das tabelas em CSV e Excel (para você ver os dados)."],
    ["docs/Desafio-RMI-Guia-101.pdf", "Este documento."],
], larguras=[6.5 * cm, 9.5 * cm]))
E.append(Spacer(1, 10))
E.append(P("Fim do guia. Qualquer conceito que ainda tenha ficado confuso pode ser aprofundado "
           "na documentação oficial do dbt (docs.getdbt.com) e do BigQuery.", st_small))

# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------
doc = BaseDocTemplate(SAIDA, pagesize=A4,
                      leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=2 * cm,
                      title="Desafio RMI - Guia 101", author="Matheus Bianco")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
doc.addPageTemplates([PageTemplate(id="base", frames=[frame], onPage=rodape)])
doc.build(E)
print("PDF gerado:", SAIDA)
