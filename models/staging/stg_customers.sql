with source as (
    select * from {{ source('northwind_raw', 'customers') }}
),

renamed as (
    select
        customer_id,
        company_name,
        contact_name,
        contact_title,
        address,
        city,
        region,
        postal_code,
        country,
        phone,
        fax
    from source
)

select * from renamed
