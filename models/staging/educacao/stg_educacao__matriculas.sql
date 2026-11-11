with

source as (
    select * from {{ source('rmi_educacao', 'turma') }}
),

renamed as (
    select
        to_hex(id_aluno)    as aluno_id,
        id_turma            as turma_id,
        ano                 as ano_letivo   -- anonimizado deterministicamente para 2000
    from source
)

-- A fonte `turma` e, na pratica, a tabela de MATRICULAS (1 linha por aluno,
-- indicando a turma do ano letivo). Renomeamos para refletir a semantica real.
select * from renamed
