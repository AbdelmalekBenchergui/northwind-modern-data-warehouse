with source as (
    select * from {{ source('northwind_raw', 'categories') }}
),

renamed as (
    select
        category_id,
        category_name,
        description
    from source
)

select * from renamed
