with source as (
    select * from {{ source('northwind_raw', 'employees') }}
),

renamed as (
    select
        employee_id,
        last_name,
        first_name,
        title,
        title_of_courtesy,
        cast(birth_date as date) as birth_date,
        cast(hire_date as date) as hire_date,
        address,
        city,
        region,
        postal_code,
        country,
        home_phone,
        extension,
        notes,
        reports_to
    from source
)

select * from renamed
