with

avaliacoes as (
    select * from {{ ref('stg_educacao__avaliacoes') }}
    where nota is not null   -- ignora disciplinas sem nota (ex: Inglês, 100% nulo)
),

-- Desempenho consolidado por aluno/turma, com medias por disciplina (pivot).
desempenho as (
    select
        aluno_id,
        turma_id,
        count(*)                                                        as n_notas,
        count(distinct bimestre)                                        as n_bimestres,
        avg(nota)                                                       as media_geral,
        avg(if(disciplina = 'Português',  nota, null))                  as media_portugues,
        avg(if(disciplina = 'Ciências',   nota, null))                  as media_ciencias,
        avg(if(disciplina = 'Inglês',     nota, null))                  as media_ingles,
        avg(if(disciplina = 'Matemática', nota, null))                  as media_matematica
    from avaliacoes
    group by aluno_id, turma_id
),

final as (
    select
        aluno_id,
        turma_id,
        n_notas,
        n_bimestres,
        round(media_geral, 2)       as media_geral,
        round(media_portugues, 2)   as media_portugues,
        round(media_ciencias, 2)    as media_ciencias,
        round(media_ingles, 2)      as media_ingles,
        round(media_matematica, 2)  as media_matematica,
        -- Regra de negocio: aprovado se media geral >= 6 (criterio comum da rede).
        media_geral >= 6            as flag_aprovado_media
    from desempenho
)

select * from final
