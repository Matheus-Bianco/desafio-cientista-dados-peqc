-- Regra de negocio / integridade: apos a deduplicacao, cada combinacao
-- (aluno, turma, escola, periodo, disciplina) deve ser unica na frequencia.
-- Garante que a logica de dedup do staging funcionou e que o grao e confiavel
-- antes de qualquer agregacao nos marts.
--
-- O teste passa quando NAO retorna linhas.

select
    aluno_id,
    turma_id,
    escola_id,
    periodo_data_inicio,
    periodo_data_fim,
    disciplina_codigo,
    count(*) as n
from {{ ref('stg_educacao__frequencia') }}
group by 1, 2, 3, 4, 5, 6
having count(*) > 1
