with

source as (
    select * from {{ source('rmi_educacao', 'frequencia') }}
),

renamed as (
    select
        id_escola                                   as escola_id,
        to_hex(id_aluno)                            as aluno_id,
        id_turma                                    as turma_id,
        safe.parse_date('%Y-%m-%d', data_inicio)    as periodo_data_inicio,
        safe.parse_date('%Y-%m-%d', data_fim)       as periodo_data_fim,
        disciplina                                  as disciplina_codigo,
        {{ nome_disciplina('disciplina') }}         as disciplina,
        frequencia                                  as percentual_frequencia
    from source
),

-- A fonte traz ~2,6 mil linhas totalmente duplicadas no grao
-- (aluno/turma/escola/periodo/disciplina). Mantemos uma unica ocorrencia.
deduplicado as (
    select
        *,
        row_number() over (
            partition by aluno_id, turma_id, escola_id,
                         periodo_data_inicio, periodo_data_fim, disciplina_codigo
            order by percentual_frequencia desc
        ) as _rn
    from renamed
)

select * except (_rn)
from deduplicado
where _rn = 1
