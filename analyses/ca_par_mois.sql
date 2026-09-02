select
    d.year,
    d.month,
    round(sum(f.revenue), 2) as ca
from {{ ref('fct_order_details') }} as f
left join {{ ref('dim_date') }} as d on f.order_date_key = d.date_key
group by d.year, d.month
order by d.year, d.month
