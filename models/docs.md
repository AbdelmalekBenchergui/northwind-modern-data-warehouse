{% docs customer_key %}
Surrogate key built from the natural `customer_id` (`dbt_utils.generate_surrogate_key`).
Links order facts to the customer dimension.
{% enddocs %}

{% docs product_key %}
Surrogate key built from the natural `product_id` (`dbt_utils.generate_surrogate_key`).
Links order facts to the product dimension.
{% enddocs %}

{% docs employee_key %}
Surrogate key built from the natural `employee_id` (`dbt_utils.generate_surrogate_key`).
Links order facts to the employee (seller) dimension.
{% enddocs %}

{% docs shipper_key %}
Surrogate key built from the natural `shipper_id` (`dbt_utils.generate_surrogate_key`).
Links order facts to the shipper (carrier) dimension.
{% enddocs %}

{% docs date_key %}
Surrogate key built from `date_day` (`dbt_utils.generate_surrogate_key`).
Links any date fact to the calendar dimension.
{% enddocs %}

{% docs order_details_key %}
Surrogate key built from the pair (`order_id`, `product_id`)
(`dbt_utils.generate_surrogate_key`). Uniquely identifies one order line.
{% enddocs %}

{% docs revenue %}
Net revenue of a line item, computed as `round(unit_price * quantity * (1 - discount), 2)`.
A `check` constraint enforces `revenue >= 0`.
{% enddocs %}

{% docs company_name %}
Company display name. When the column is prefixed (e.g. `supplier_company_name`) it is the
denormalized copy of the related party.
{% enddocs %}

{% docs contact_name %}
Name of the primary contact person.
{% enddocs %}

{% docs contact_title %}
Business title / role of the primary contact person.
{% enddocs %}

{% docs address %}
Street address (first line).
{% enddocs %}

{% docs city %}
City of the address.
{% enddocs %}

{% docs region %}
State, province or region of the address. May be `null` when not applicable.
{% enddocs %}

{% docs postal_code %}
Postal or ZIP code of the address.
{% enddocs %}

{% docs country %}
Country of the address.
{% enddocs %}

{% docs phone %}
Primary telephone number.
{% enddocs %}

{% docs fax %}
Fax number. May be `null` when the company has none.
{% enddocs %}

{% docs quantity_per_unit %}
Packaging / quantity description of the product, e.g. `"10 boxes x 30 bags"`.
{% enddocs %}

{% docs unit_price %}
List price of one unit of the product (product master), or unit price applied on the order line.
{% enddocs %}

{% docs units_in_stock %}
Current number of units in stock.
{% enddocs %}

{% docs units_on_order %}
Number of units currently on order from the supplier.
{% enddocs %}

{% docs reorder_level %}
Stock level below which the product should be reordered.
{% enddocs %}

{% docs discontinued %}
Flag (`0` = active, `1` = discontinued). Kept as an integer to mirror the raw source.
{% enddocs %}

{% docs category_name %}
Name of the product category.
{% enddocs %}

{% docs category_description %}
Free-text description of the product category (documentation only, no business logic).
{% enddocs %}

{% docs product_name %}
Display name of the product.
{% enddocs %}

{% docs quantity %}
Number of units ordered for this line. A `check` constraint enforces `quantity >= 1`.
{% enddocs %}

{% docs discount %}
Discount rate applied to the line, between `0` and `1` (enforced by `check` constraint).
{% enddocs %}

{% docs employees_last_name %}
Employee's surname.
{% enddocs %}

{% docs employees_first_name %}
Employee's given name.
{% enddocs %}

{% docs title_employee %}
Employee's job title.
{% enddocs %}

{% docs title_of_courtesy %}
Form of address for the employee (e.g. `Ms.`, `Dr.`).
{% enddocs %}

{% docs birth_date %}
Employee's date of birth.
{% enddocs %}

{% docs hire_date %}
Date the employee joined the company.
{% enddocs %}

{% docs home_phone %}
Employee's personal telephone number.
{% enddocs %}

{% docs extension %}
Employee's phone extension (kept as a string to preserve leading zeros).
{% enddocs %}

{% docs notes %}
Free-text HR notes about the employee (no business logic).
{% enddocs %}

{% docs manager_key %}
Surrogate key of the employee's manager, built from the manager's natural `employee_id`
(`reports_to`). `null` for the top of the hierarchy.
{% enddocs %}

{% docs manager_name %}
Display name of the employee's manager as `"<first_name> <last_name>"`. `null` when the
employee is the top of the hierarchy. A test ensures no employee reports to themselves.
{% enddocs %}

{% docs is_weekend %}
Flag (`0` = weekday, `1` = Saturday or Sunday).
{% enddocs %}

{% docs snap_customers_description %}
Type-2 (check strategy) snapshot of customers. Keeps history of every change to the
customer profile attributes, adding `dbt_valid_from` / `dbt_valid_to` audit columns.
{% enddocs %}

{% docs snap_products_description %}
Type-2 (check strategy) snapshot of products. Keeps history of every change to the product
master, adding `dbt_valid_from` / `dbt_valid_to` audit columns.
{% enddocs %}