with source as (
    select * from {{ source('northwind_raw', 'order_details') }}
),

renamed as (
    select
        order_id,
        product_id,
        cast(unit_price as numeric(10, 2)) as unit_price,
        quantity,
        cast(discount as numeric(4, 2)) as discount
    from source
)

select * from renamed
