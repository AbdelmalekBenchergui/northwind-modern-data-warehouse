with fct as (
    select * from {{ ref('fct_order_details') }}
)

select
    {{ dbt_utils.star(ref('fct_order_details'), relation_alias='fct') }},
    {{ dbt_utils.star(ref('dim_customer'), relation_alias='customer', except=['customer_key'], prefix='customer_') }},
    {{ dbt_utils.star(ref('dim_product'), relation_alias='product', except=['product_key', 'unit_price'], prefix='product_') }},
    product.unit_price as product_unit_price,
    {{ dbt_utils.star(ref('dim_employee'), relation_alias='employee', except=['employee_key'], prefix='employee_') }},
    {{ dbt_utils.star(ref('dim_shipper'), relation_alias='shipper', except=['shipper_key'], prefix='shipper_') }},
    {{ dbt_utils.star(ref('dim_date'), relation_alias='order_date', except=['date_key', 'date_day'], prefix='order_date_') }},
    order_date.date_day as order_date,
    {{ dbt_utils.star(ref('dim_date'), relation_alias='required_date', except=['date_key', 'date_day'], prefix='required_date_') }},
    required_date.date_day as required_date,
    {{ dbt_utils.star(ref('dim_date'), relation_alias='shipped_date', except=['date_key', 'date_day'], prefix='shipped_date_') }},
    shipped_date.date_day as shipped_date
from fct
left join {{ ref('dim_customer') }} as customer on fct.customer_key = customer.customer_key
left join {{ ref('dim_product') }} as product on fct.product_key = product.product_key
left join {{ ref('dim_employee') }} as employee on fct.employee_key = employee.employee_key
left join {{ ref('dim_shipper') }} as shipper on fct.shipper_key = shipper.shipper_key
left join {{ ref('dim_date') }} as order_date on fct.order_date_key = order_date.date_key
left join {{ ref('dim_date') }} as required_date on fct.required_date_key = required_date.date_key
left join {{ ref('dim_date') }} as shipped_date on fct.shipped_date_key = shipped_date.date_key
