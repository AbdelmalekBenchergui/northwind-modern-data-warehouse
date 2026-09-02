with ca_mensuel as (
    select
        d.year,
        d.month,
        round(sum(f.revenue), 2) as ca
    from {{ ref('fct_order_details') }} as f
    left join {{ ref('dim_date') }} as d on f.order_date_key = d.date_key
    group by d.year, d.month
)

select
    year,
    month,
    ca,
    round(sum(ca) over (order by year, month), 2) as ca_cumule
from ca_mensuel
order by year, month
