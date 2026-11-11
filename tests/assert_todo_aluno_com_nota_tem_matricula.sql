-- Regra de negocio: nenhum aluno pode ter nota lancada sem possuir matricula.
-- Uma avaliacao "orfa" (sem aluno correspondente na matricula) indicaria
-- lancamento indevido ou falha de integracao entre os sistemas de origem.
--
-- O teste passa quando NAO retorna linhas.

with avaliacoes as (
    select distinct aluno_id
    from {{ ref('stg_educacao__avaliacoes') }}
    where nota is not null
),

matriculas as (
    select distinct aluno_id
    from {{ ref('stg_educacao__matriculas') }}
)

select a.aluno_id
from avaliacoes a
left join matriculas m on a.aluno_id = m.aluno_id
where m.aluno_id is null
