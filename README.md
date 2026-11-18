# Retail Sales Analytics — Interview Practice Project

A compact, runnable end-to-end analytics case for a Trainee Data Analytics interview. It uses synthetic retail data and only Python's standard library, so it runs without installing packages.

## Business question

> Which regions and product categories are contributing the most net sales and profit, and what should the business investigate next?

The project is intentionally small enough to explain at a whiteboard. Do not claim that its synthetic results describe a real company.

## Run it

From this folder:

```powershell
& "C:/Program Files/Python313/python.exe" .\analysis.py
```

Or, if `python` is on your PATH:

```powershell
python .\analysis.py
```

The script loads `data\sales.csv`, reports quality issues, excludes invalid/duplicate transactions according to the policy below, loads valid rows into an in-memory SQLite database, and prints KPI, category, region, and monthly summaries.

## Exact analysis flow

1. **Clarify the decision.** Confirm the business question, time period, currency, grain, and definitions with the stakeholder. Here, one row is one order line; one order may have multiple lines in a real dataset.
2. **Inspect the source.** Check column names/types, date range, row count, grain, missing values, duplicates, and implausible values before calculating anything.
3. **Clean transparently.** This demo skips rows with missing required fields, invalid numbers/dates, out-of-range discounts, non-positive units, or repeated `order_id`. In a real project, first establish whether the ID identifies an order or an order line; deduplicating on the wrong key can delete valid data. This sample assumes one row per order.
4. **Create derived measures.**
   - Gross sales = `units × unit_price`
   - Net sales = `gross sales × (1 − discount_pct)`
   - Cost = `units × unit_cost`
   - Profit = `net sales − cost`
   - Profit margin = `profit ÷ net sales` (guard against zero net sales)
5. **Aggregate at useful levels.** Calculate overall KPIs, then compare category, region, and month. Always state whether averages are weighted: overall margin is total profit divided by total net sales, not the unweighted average of segment margins.
6. **Check the result.** Reconcile row counts and totals; inspect extremes; compare a hand-calculated row; make sure segment totals reconcile to the overall total. Look for data leakage or inconsistent date/currency definitions.
7. **Communicate an action.** State the finding, its business impact, a recommended next analysis/action, and a limitation. Do not claim that a pattern proves causation.

## SQL practice

`analysis.sql` contains SQLite queries over the cleaned `sales` table used by the Python script. It demonstrates `SUM`, `COUNT`, `GROUP BY`, date grouping, `CASE`, and a window function. Try changing the query before reading the result. Example questions:

- Which category has the most net sales? Which has the best margin?
- Do high-discount transactions appear to have lower margins? Why is that association not proof that discounts caused lower profit?
- How would you rank categories within each region?
- How would you handle returns, nulls, multiple order lines, or a month with no sales?

## Python and pandas translation

The runnable script uses `csv`, `datetime`, and `sqlite3` to avoid dependency setup. In an interview, describe the equivalent pandas workflow:

```python
df = pd.read_csv("data/sales.csv", parse_dates=["date"])
df.info()
df.isna().sum()
df.duplicated(subset=["order_id"]).sum()
df = df.drop_duplicates(subset=["order_id"])
df["net_sales"] = df["units"] * df["unit_price"] * (1 - df["discount_pct"])
summary = df.groupby("category", as_index=False).agg(
    net_sales=("net_sales", "sum"),
    orders=("order_id", "nunique"),
)
```

That snippet is an illustration, not part of the runnable project; agree on the duplicate key and missing-value policy before dropping anything.

## Core concepts to revise tonight

### SQL

- `SELECT`, `WHERE`, `ORDER BY`, `GROUP BY`, `HAVING`
- `INNER JOIN` vs `LEFT JOIN`; join keys and row multiplication
- `COUNT(*)` vs `COUNT(DISTINCT order_id)`; `NULL` behavior
- `CASE WHEN`, `COALESCE`, date grouping, CTEs
- Window functions such as `ROW_NUMBER()` and `RANK()`
- Safe division using `numerator / NULLIF(denominator, 0)`

**Join trap:** if an order has multiple line items and you join it to a table with multiple matching payments, the result can multiply rows and inflate sums. Check key uniqueness and row counts before/after joins.

### Excel

- Tables, sort/filter, remove duplicates (only after validating the key)
- `SUMIFS`, `COUNTIFS`, `XLOOKUP`, `IFERROR`, date/text functions
- PivotTables for category/region/month comparisons
- Absolute vs relative references; percentages and number formats
- Validate totals before presenting; avoid hiding rows that affect the result

### Statistics and business reasoning

- Mean vs median; outliers and skew
- Population vs sample; sampling bias
- Correlation is not causation; confounders and experiments
- Percentage change = `(new − old) / old`; be careful when the baseline is zero/negative
- Revenue/sales is not profit; margin is not the same as profit
- Segment comparisons need comparable time periods and denominators

### Dashboard and communication

- Start with a decision and audience, not a chart
- Show a few defined KPIs, trend, and useful breakdowns
- Use readable axes, consistent units, meaningful labels, and filters
- Add context/targets; avoid misleading truncated axes and decorative charts
- End with a recommendation and limitations

## Interview-ready project explanation (about 60–90 seconds)

> “I built a small retail sales analysis around the question of which categories and regions contribute net sales and profit. I first checked the transaction grain, dates, missing values, duplicate IDs, and numeric ranges. I documented the cleaning rules instead of silently changing the data. Then I calculated net sales after discounts, cost, profit, and weighted margin, and used SQLite groupings to compare categories, regions, and months. I checked that segment totals reconciled to the overall totals. My next step would be to validate the definitions with a stakeholder and investigate discounting, returns, and seasonality before recommending a pricing action. The dataset is synthetic, so I would not present these numbers as real business findings.”

Replace that last sentence with a truthful description of what you actually ran and learned.

## Likely questions: answer with this structure

1. **How do you approach a new dataset?** Clarify decision/grain/definitions → profile → clean/document → analyze → validate → communicate.
2. **How would you handle missing data?** Find where/why it is missing; assess impact; choose a documented drop, imputation, or “unknown” category based on meaning; report coverage.
3. **How do you find a cause for a sales drop?** Confirm data quality and comparable periods, decompose by product/region/channel/price/volume, form hypotheses, then test with an experiment or stronger causal design.
4. **What is a KPI?** A measurable indicator tied to a goal, with a precise formula, scope, owner, and reporting cadence.
5. **What if SQL and Excel totals differ?** Check filters, join cardinality, duplicate keys, nulls, date boundaries, rounding, and metric definitions; reconcile with a small sample.
6. **What is your weakness / why this role?** Use a genuine example; explain what you are learning and why this trainee role matches your interests. Do not invent company facts.

