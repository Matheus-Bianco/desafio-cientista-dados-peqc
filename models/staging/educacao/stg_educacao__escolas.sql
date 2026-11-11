with

source as (
    select * from {{ source('rmi_educacao', 'escola') }}
),

renamed as (
    select
        id_escola   as escola_id,
        bairro      as bairro_id
    from source
)

select * from renamed
