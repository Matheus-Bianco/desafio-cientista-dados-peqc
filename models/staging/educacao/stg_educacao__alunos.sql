with

source as (
    select * from {{ source('rmi_educacao', 'aluno') }}
),

renamed as (
    select
        -- id_aluno vem como BYTES (hash de 17 bytes). Convertemos para STRING
        -- hexadecimal: chave estavel, legivel e compativel entre todas as tabelas.
        to_hex(id_aluno)                    as aluno_id,
        id_turma                            as turma_id,
        nullif(trim(faixa_etaria), '')      as faixa_etaria,
        bairro                              as bairro_id
    from source
)

select * from renamed
