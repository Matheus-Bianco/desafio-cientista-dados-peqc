{#
    Mapeia o codigo generico de disciplina (disciplina_1..4) para o nome
    legivel. Centraliza a regra em um unico lugar, evitando repetir o CASE
    em varios models (DRY). O de/para tambem existe como seed
    (seed_educacao__disciplinas) para fins de documentacao e relationships.
#}
{% macro nome_disciplina(coluna) %}
    case {{ coluna }}
        when 'disciplina_1' then 'Português'
        when 'disciplina_2' then 'Ciências'
        when 'disciplina_3' then 'Inglês'
        when 'disciplina_4' then 'Matemática'
        else 'Desconhecida'
    end
{% endmacro %}
