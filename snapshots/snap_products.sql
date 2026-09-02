{% snapshot snap_products %}

{{
    config(
        target_schema='snapshots',
        unique_key='product_id',
        strategy='check',
        check_cols=['product_name', 'supplier_id', 'category_id', 'quantity_per_unit', 'unit_price', 'units_in_stock', 'units_on_order', 'reorder_level', 'discontinued']
    )
}}

    select * from {{ ref('stg_products') }}

{% endsnapshot %}
