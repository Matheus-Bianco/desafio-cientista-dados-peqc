with

avaliacoes as (
    select * from {{ ref('stg_educacao__avaliacoes') }}
),

frequencia as (
    select * from {{ ref('stg_educacao__frequencia') }}
),

alunos as (
    select * from {{ ref('stg_educacao__alunos') }}
),

-- FONTE DE FREQUENCIA COM SINAL REAL.
-- Existem dois campos de frequencia na base: (1) a tabela `frequencia`, por
-- periodo/disciplina, que nos dados anonimizados fica travada entre 97% e 100%
-- (sem variancia); e (2) a coluna `frequencia` da `avaliacao`, geral por
-- bimestre, que varia de 0 a 100 (media ~89%, desvio ~12). Usamos a (2) para
-- medir absenteismo, pois e a unica com variacao analisavel. Ver README.
-- Grao da fonte: aluno/turma/bimestre (deduplicado do formato long).
freq_bimestral as (
    select distinct
        aluno_id,
        turma_id,
        bimestre,
        frequencia_bimestre_origem as frequencia_bimestre
    from avaliacoes
    where frequencia_bimestre_origem is not null
),

frequencia_por_aluno as (
    select
        aluno_id,
        count(*)                        as n_bimestres_com_frequencia,
        avg(frequencia_bimestre)        as media_frequencia,
        min(frequencia_bimestre)        as min_frequencia,
        max(frequencia_bimestre)        as max_frequencia
    from freq_bimestral
    group by aluno_id
),

-- Frequencia da tabela `frequencia` (sem variancia): mantida apenas como
-- contraste/transparencia, NAO usada para o flag de absenteismo.
frequencia_registros_por_aluno as (
    select
        aluno_id,
        count(*)                        as n_registros_frequencia,
        avg(percentual_frequencia)      as media_frequencia_registros
    from frequencia
    group by aluno_id
),

-- Escola predominante do aluno (chave de escola confiavel, concilia 100%),
-- usada para atribuir regiao no mart de absenteismo.
escola_predominante as (
    select
        aluno_id,
        escola_id
    from (
        select
            aluno_id,
            escola_id,
            row_number() over (
                partition by aluno_id
                order by count(*) desc, escola_id
            ) as rn
        from frequencia
        group by aluno_id, escola_id
    )
    where rn = 1
),

final as (
    select
        a.aluno_id,
        a.faixa_etaria,
        a.turma_id                                      as turma_id_matricula,
        ep.escola_id,
        -- frequencia com sinal (avaliacao.frequencia)
        fa.n_bimestres_com_frequencia,
        round(fa.media_frequencia, 2)                   as media_frequencia,
        round(fa.min_frequencia, 2)                     as min_frequencia,
        round(fa.max_frequencia, 2)                     as max_frequencia,
        -- frequencia da tabela `frequencia` (contraste, sem variancia)
        fr.n_registros_frequencia,
        round(fr.media_frequencia_registros, 2)         as media_frequencia_registros,
        -- Regra de negocio: absenteismo cronico = frequencia media (bimestral)
        -- abaixo do limite de politica educacional.
        fa.media_frequencia < {{ var('limite_frequencia_adequada') }} as flag_absenteismo_cronico
    from alunos a
    left join frequencia_por_aluno fa            on a.aluno_id = fa.aluno_id
    left join frequencia_registros_por_aluno fr  on a.aluno_id = fr.aluno_id
    left join escola_predominante ep             on a.aluno_id = ep.aluno_id
)

select * from final
