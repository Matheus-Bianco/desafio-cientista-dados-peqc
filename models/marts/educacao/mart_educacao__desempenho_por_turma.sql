{{ config(materialized = 'table') }}

-- Pergunta de negocio: como o tamanho da turma se relaciona com o desempenho
-- medio nas avaliacoes? (O README sugere tambem serie/turno, mas esses campos
-- NAO existem nos dados; usamos o tamanho da turma, que e derivavel da matricula.)

with

matriculas as (
    select * from {{ ref('stg_educacao__matriculas') }}
),

desempenho as (
    select * from {{ ref('int_educacao__aluno_desempenho') }}
),

-- Tamanho da turma = numero de alunos matriculados.
tamanho_turma as (
    select
        turma_id,
        count(*) as n_alunos_matriculados
    from matriculas
    group by turma_id
),

desempenho_turma as (
    select
        turma_id,
        count(distinct aluno_id)        as n_alunos_avaliados,
        round(avg(media_geral), 2)      as media_geral_turma,
        round(avg(media_portugues), 2)  as media_portugues,
        round(avg(media_ciencias), 2)   as media_ciencias,
        round(avg(media_matematica), 2) as media_matematica,
        round(avg(if(flag_aprovado_media, 1, 0)), 4) as taxa_aprovacao_media
    from desempenho
    group by turma_id
),

final as (
    select
        t.turma_id,
        t.n_alunos_matriculados,
        case
            when t.n_alunos_matriculados <= 5  then '01. Ate 5 alunos'
            when t.n_alunos_matriculados <= 10 then '02. 6 a 10 alunos'
            when t.n_alunos_matriculados <= 20 then '03. 11 a 20 alunos'
            when t.n_alunos_matriculados <= 30 then '04. 21 a 30 alunos'
            else '05. Mais de 30 alunos'
        end                                     as faixa_tamanho_turma,
        d.n_alunos_avaliados,
        d.media_geral_turma,
        d.media_portugues,
        d.media_ciencias,
        d.media_matematica,
        d.taxa_aprovacao_media
    from tamanho_turma t
    left join desempenho_turma d on t.turma_id = d.turma_id
)

select * from final
order by n_alunos_matriculados desc
