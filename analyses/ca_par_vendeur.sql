select
    e.first_name || ' ' || e.last_name as vendeur,
    round(sum(f.revenue), 2) as ca
from {{ ref('fct_order_details') }} as f
left join {{ ref('dim_employee') }} as e on f.employee_key = e.employee_key
group by e.first_name, e.last_name
order by ca desc
