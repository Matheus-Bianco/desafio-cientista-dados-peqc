with

source as (
    select * from {{ source('rmi_educacao', 'avaliacao') }}
),

renamed as (
    select
        to_hex(id_aluno)        as aluno_id,
        id_turma                as turma_id,
        cast(bimestre as int64) as bimestre,
        -- Campo original da fonte (frequencia geral do bimestre, 0 a 100).
        -- Preenchido em ~99,2% das linhas; mantido para rastreabilidade.
        frequencia              as frequencia_bimestre_origem,
        disciplina_1,
        disciplina_2,
        disciplina_3,
        disciplina_4
    from source
),

-- A fonte vem em formato WIDE (uma coluna por disciplina). Normalizamos para
-- LONG (1 linha por aluno/turma/bimestre/disciplina) com UNPIVOT.
-- Usamos INCLUDE NULLS para preservar a estrutura (ex: Inglês, 100% nulo),
-- permitindo auditar explicitamente a ausencia de notas.
unpivotado as (
    select
        aluno_id,
        turma_id,
        bimestre,
        frequencia_bimestre_origem,
        disciplina_codigo,
        nota
    from renamed
    unpivot include nulls (
        nota for disciplina_codigo in (
            disciplina_1, disciplina_2, disciplina_3, disciplina_4
        )
    )
),

final as (
    select
        aluno_id,
        turma_id,
        bimestre,
        frequencia_bimestre_origem,
        disciplina_codigo,
        {{ nome_disciplina('disciplina_codigo') }} as disciplina,
        nota
    from unpivotado
),

-- ~34 duplicatas de grao na fonte (aluno/turma/bimestre/disciplina).
deduplicado as (
    select
        *,
        row_number() over (
            partition by aluno_id, turma_id, bimestre, disciplina_codigo
            order by nota desc
        ) as _rn
    from final
)

select * except (_rn)
from deduplicado
where _rn = 1
