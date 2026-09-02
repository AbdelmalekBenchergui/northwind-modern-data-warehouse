{{
    config(
        materialized='incremental',
        unique_key='order_details_key',
        incremental_strategy='delete+insert',
        on_schema_change='fail'
    )
}}

with stg_order_details as (
    select * from {{ ref('stg_order_details') }}
),

stg_orders as (
    select * from {{ ref('stg_orders') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['od.order_id', 'od.product_id']) }} as order_details_key,
    od.order_id,
    {{ dbt_utils.generate_surrogate_key(['o.customer_id']) }} as customer_key,
    {{ dbt_utils.generate_surrogate_key(['od.product_id']) }} as product_key,
    {{ dbt_utils.generate_surrogate_key(['o.employee_id']) }} as employee_key,
    {{ dbt_utils.generate_surrogate_key(['o.ship_via']) }} as shipper_key,
    {{ dbt_utils.generate_surrogate_key(['o.order_date']) }} as order_date_key,
    {{ dbt_utils.generate_surrogate_key(['o.required_date']) }} as required_date_key,
    case
        when o.shipped_date is null then null
        else {{ dbt_utils.generate_surrogate_key(['o.shipped_date']) }}
    end as shipped_date_key,
    od.quantity,
    od.unit_price,
    od.discount,
    round(od.unit_price * od.quantity * (1 - od.discount), 2) as revenue
from stg_order_details as od
left join stg_orders as o on od.order_id = o.order_id
{% if is_incremental() %}
    where od.order_id > (select max(order_id) from {{ this }})
{% endif %}
