with stg_products as (
    select * from {{ ref('stg_products') }}
),

stg_categories as (
    select * from {{ ref('stg_categories') }}
),

stg_suppliers as (
    select * from {{ ref('stg_suppliers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['p.product_id']) }} as product_key,
    p.product_id,
    p.product_name,
    p.quantity_per_unit,
    p.unit_price,
    p.units_in_stock,
    p.units_on_order,
    p.reorder_level,
    p.discontinued,
    c.category_id,
    c.category_name,
    c.description as category_description,
    s.supplier_id,
    s.company_name as supplier_company_name,
    s.contact_name as supplier_contact_name,
    s.contact_title as supplier_contact_title,
    s.address as supplier_address,
    s.city as supplier_city,
    s.region as supplier_region,
    s.postal_code as supplier_postal_code,
    s.country as supplier_country,
    s.phone as supplier_phone
from stg_products as p
left join stg_categories as c on p.category_id = c.category_id
left join stg_suppliers as s on p.supplier_id = s.supplier_id
