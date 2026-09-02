with stg_date as (
    select * from {{ ref('stg_date') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['date_day']) }} as date_key,
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
from stg_date
