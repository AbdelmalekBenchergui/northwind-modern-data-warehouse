with source as (
    select * from {{ source('northwind_raw', 'date') }}
),

renamed as (
    select
        date_day,
        year,
        quarter,
        month,
        month_name,
        day_of_week,
        day_of_week_name,
        day_of_month,
        day_of_year,
        is_weekend
    from source
)

select * from renamed
