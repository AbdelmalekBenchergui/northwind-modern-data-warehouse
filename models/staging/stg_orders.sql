with source as (
    select * from {{ source('northwind_raw', 'orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        employee_id,
        cast(order_date as date) as order_date,
        cast(required_date as date) as required_date,
        cast(shipped_date as date) as shipped_date,
        ship_via,
        cast(freight as numeric(10, 2)) as freight,
        ship_name,
        ship_address,
        ship_city,
        ship_region,
        ship_postal_code,
        ship_country
    from source
)

select * from renamed
