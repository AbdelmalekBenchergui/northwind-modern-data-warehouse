with source as (
    select * from {{ source('northwind_raw', 'products') }}
),

renamed as (
    select
        product_id,
        product_name,
        supplier_id,
        category_id,
        quantity_per_unit,
        cast(unit_price as numeric(10, 2)) as unit_price,
        units_in_stock,
        units_on_order,
        reorder_level,
        discontinued
    from source
)

select * from renamed
