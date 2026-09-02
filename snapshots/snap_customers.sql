{% snapshot snap_customers %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=['company_name', 'contact_name', 'contact_title', 'address', 'city', 'region', 'postal_code', 'country', 'phone', 'fax']
    )
}}

    select * from {{ ref('stg_customers') }}

{% endsnapshot %}