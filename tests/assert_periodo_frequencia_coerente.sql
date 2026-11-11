-- Regra de negocio: o inicio do periodo de apuracao de frequencia nunca pode
-- ser posterior ao fim do periodo. Um registro com data_inicio > data_fim
-- indica erro de ETL/origem e invalidaria qualquer calculo temporal.
--
-- O teste passa quando NAO retorna linhas.

select
    aluno_id,
    turma_id,
    periodo_data_inicio,
    periodo_data_fim
from {{ ref('stg_educacao__frequencia') }}
where periodo_data_inicio is not null
  and periodo_data_fim is not null
  and periodo_data_inicio > periodo_data_fim
