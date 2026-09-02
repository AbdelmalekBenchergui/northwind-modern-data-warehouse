select
    s.company_name as transporteur,
    round(sum(f.revenue), 2) as ca
from {{ ref('fct_order_details') }} as f
left join {{ ref('dim_shipper') }} as s on f.shipper_key = s.shipper_key
group by s.company_name
order by ca desc
