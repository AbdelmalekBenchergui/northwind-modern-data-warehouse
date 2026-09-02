select
    p.category_name,
    round(sum(f.revenue), 2) as ca
from {{ ref('fct_order_details') }} as f
left join {{ ref('dim_product') }} as p on f.product_key = p.product_key
group by p.category_name
order by ca desc
