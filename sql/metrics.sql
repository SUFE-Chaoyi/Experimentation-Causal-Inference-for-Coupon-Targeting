-- Example SQL for interview discussion: build pre-period customer metrics.
WITH tx AS (
    SELECT
        customer_id,
        invoice_no,
        invoice_date,
        quantity,
        unit_price,
        quantity * unit_price AS revenue,
        country
    FROM online_retail_transactions
    WHERE customer_id IS NOT NULL
      AND quantity > 0
      AND unit_price > 0
      AND LOWER(invoice_no) NOT LIKE 'c%'
), pre_period AS (
    SELECT *
    FROM tx
    WHERE invoice_date < DATE '2011-09-01'
)
SELECT
    customer_id,
    COUNT(DISTINCT invoice_no) AS pre_orders,
    SUM(quantity) AS pre_items,
    SUM(revenue) AS pre_revenue,
    AVG(revenue) AS pre_avg_basket,
    MAX(invoice_date) AS pre_last_date,
    ANY_VALUE(country) AS country
FROM pre_period
GROUP BY 1;
