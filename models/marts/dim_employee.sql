with stg_employees as (
    select * from {{ ref('stg_employees') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['e.employee_id']) }} as employee_key,
    e.employee_id,
    e.last_name,
    e.first_name,
    e.title,
    e.title_of_courtesy,
    e.birth_date,
    e.hire_date,
    e.address,
    e.city,
    e.region,
    e.postal_code,
    e.country,
    e.home_phone,
    e.extension,
    e.notes,
    case
        when e.reports_to is null then null
        else {{ dbt_utils.generate_surrogate_key(['e.reports_to']) }}
    end as manager_key,
    manager.first_name || ' ' || manager.last_name as manager_name
from stg_employees as e
left join stg_employees as manager on e.reports_to = manager.employee_id
