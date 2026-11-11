{{
    config(
        materialized = 'table',
        cluster_by = ['bairro_id']
    )
}}

-- Pergunta de negocio: quais escolas/regioes concentram maior taxa de alunos
-- com absenteismo cronico (frequencia media abaixo de 75%)?
--
-- DECISAO ANALITICA (ver README): a base tem dois campos de frequencia. A
-- tabela `frequencia` (por periodo) nao tem variancia (97%-100%), entao daria
-- taxa zero em toda a rede. A frequencia GERAL por bimestre (avaliacao.frequencia)
-- varia de 0 a 100 e e a que carrega sinal. Este mart usa a frequencia com sinal
-- para o flag de absenteismo e expoe tambem a frequencia por registro como
-- contraste/transparencia.

with

aluno_frequencia as (
    select * from {{ ref('int_educacao__aluno_frequencia') }}
),

escolas as (
    select * from {{ ref('stg_educacao__escolas') }}
),

agregado as (
    select
        e.bairro_id,
        af.escola_id,
        count(*)                                                     as n_alunos,
        countif(af.media_frequencia is not null)                     as n_alunos_com_frequencia,
        countif(af.flag_absenteismo_cronico)                         as n_alunos_absenteismo_cronico,
        round(avg(af.media_frequencia), 2)                           as media_frequencia_regiao,
        round(min(af.media_frequencia), 2)                           as pior_frequencia_media_aluno,
        -- contraste: frequencia da tabela `frequencia` (sem variancia)
        round(avg(af.media_frequencia_registros), 2)                 as media_frequencia_registros_regiao
    from aluno_frequencia af
    left join escolas e on af.escola_id = e.escola_id
    where af.escola_id is not null
    group by e.bairro_id, af.escola_id
),

final as (
    select
        *,
        round(
            safe_divide(n_alunos_absenteismo_cronico, n_alunos_com_frequencia),
            4
        ) as taxa_absenteismo_cronico
    from agregado
)

-- Sem ORDER BY: o BigQuery nao permite ordenar o resultado de uma tabela
-- clusterizada. A ordenacao fica a cargo da consulta de consumo.
select * from final
