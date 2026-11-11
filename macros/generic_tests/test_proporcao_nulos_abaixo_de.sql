{#
    Teste GENERICO customizado: valida que a proporcao de valores nulos de uma
    coluna nao ultrapassa um limite (threshold, entre 0 e 1).

    Diferente de `not_null` (que exige ZERO nulos), este teste permite tolerar
    uma fracao de nulos conhecida e aceitavel, falhando/avisando apenas quando
    a qualidade se degrada alem do esperado. Util para monitorar colunas que
    sabidamente tem nulos (ex: bairro do aluno) sem travar o pipeline.

    Uso no schema.yml:
        columns:
          - name: bairro_id
            tests:
              - proporcao_nulos_abaixo_de:
                  threshold: 0.05
                  config:
                    severity: warn

    O teste passa quando NAO retorna linhas (proporcao <= threshold).
#}
{% test proporcao_nulos_abaixo_de(model, column_name, threshold=0.0) %}

with contagem as (
    select
        count(*)                                          as total,
        count(*) - count({{ column_name }})               as nulos
    from {{ model }}
)

select
    total,
    nulos,
    safe_divide(nulos, total) as proporcao_nulos,
    {{ threshold }}           as threshold
from contagem
where safe_divide(nulos, total) > {{ threshold }}

{% endtest %}
