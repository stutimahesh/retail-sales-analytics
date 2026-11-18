-- Run against the cleaned SQLite `sales` table created by analysis.py.
-- Metric definitions are deliberately explicit to avoid mixing gross/net sales.

-- Overall KPIs; margin is weighted as total profit / total net sales.
SELECT
    COUNT(*) AS orders,
    SUM(units * unit_price * (1 - discount_pct)) AS net_sales,
    SUM(units * unit_price * (1 - discount_pct) - units * unit_cost) AS profit,
    1.0 * SUM(units * unit_price * (1 - discount_pct) - units * unit_cost)
        / NULLIF(SUM(units * unit_price * (1 - discount_pct)), 0) AS profit_margin
FROM sales;

-- Compare sales and margin by category.
SELECT
    category,
    SUM(units * unit_price * (1 - discount_pct)) AS net_sales,
    SUM(units * unit_price * (1 - discount_pct) - units * unit_cost) AS profit,
    1.0 * SUM(units * unit_price * (1 - discount_pct) - units * unit_cost)
        / NULLIF(SUM(units * unit_price * (1 - discount_pct)), 0) AS profit_margin
FROM sales
GROUP BY category
ORDER BY net_sales DESC;

-- Rank categories within each region (window function).
WITH category_profit AS (
    SELECT
        region,
        category,
        SUM(units * unit_price * (1 - discount_pct) - units * unit_cost) AS profit
    FROM sales
    GROUP BY region, category
)
SELECT
    region,
    category,
    profit,
    RANK() OVER (PARTITION BY region ORDER BY profit DESC) AS profit_rank
FROM category_profit
ORDER BY region, profit_rank;

-- Monthly trend, suitable for a line chart after checking date coverage.
SELECT
    substr(date, 1, 7) AS month,
    SUM(units * unit_price * (1 - discount_pct)) AS net_sales
FROM sales
GROUP BY substr(date, 1, 7)
ORDER BY month;
