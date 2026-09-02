select
    c.country,
    round(sum(f.revenue), 2) as ca
from {{ ref('fct_order_details') }} as f
left join {{ ref('dim_customer') }} as c on f.customer_key = c.customer_key
group by c.country
order by ca desc
