"""Run a small, auditable retail sales analysis using only Python's standard library."""

import csv
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path


DATA_PATH = Path(__file__).parent / "data" / "sales.csv"
REQUIRED_FIELDS = (
    "order_id",
    "date",
    "region",
    "category",
    "product",
    "units",
    "unit_price",
    "discount_pct",
    "unit_cost",
)


def load_rows(path: Path) -> tuple[list[dict[str, object]], Counter[str], int]:
    """Load rows, count quality issues, and retain valid unique orders."""
    issues: Counter[str] = Counter()
    accepted: list[dict[str, object]] = []
    seen_orders: set[str] = set()

    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or any(field not in reader.fieldnames for field in REQUIRED_FIELDS):
            raise ValueError(f"CSV must contain these columns: {', '.join(REQUIRED_FIELDS)}")
        raw_count = 0

        for row in reader:
            raw_count += 1
            if any(not (row.get(field) or "").strip() for field in REQUIRED_FIELDS):
                issues["missing_required"] += 1
                continue

            order_id = row["order_id"].strip()
            if order_id in seen_orders:
                issues["duplicate_order_id"] += 1
                continue

            try:
                order_date = date.fromisoformat(row["date"].strip())
                units = int(row["units"])
                unit_price = float(row["unit_price"])
                discount_pct = float(row["discount_pct"])
                unit_cost = float(row["unit_cost"])
            except ValueError:
                issues["invalid_value"] += 1
                continue

            if units <= 0 or unit_price < 0 or unit_cost < 0 or not 0 <= discount_pct <= 1:
                issues["out_of_range"] += 1
                continue

            seen_orders.add(order_id)
            accepted.append(
                {
                    "order_id": order_id,
                    "date": order_date.isoformat(),
                    "region": row["region"].strip(),
                    "category": row["category"].strip(),
                    "product": row["product"].strip(),
                    "units": units,
                    "unit_price": unit_price,
                    "discount_pct": discount_pct,
                    "unit_cost": unit_cost,
                }
            )
    return accepted, issues, raw_count


def main() -> None:
    rows, issues, raw_count = load_rows(DATA_PATH)
    if not rows:
        raise ValueError("No valid rows remain after data-quality checks.")

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE sales (
            order_id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            region TEXT NOT NULL,
            category TEXT NOT NULL,
            product TEXT NOT NULL,
            units INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount_pct REAL NOT NULL,
            unit_cost REAL NOT NULL
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO sales VALUES (
            :order_id, :date, :region, :category, :product,
            :units, :unit_price, :discount_pct, :unit_cost
        )
        """,
        rows,
    )

    print("DATA QUALITY")
    print(f"Rows read: {raw_count} | Valid unique orders: {len(rows)}")
    if issues:
        for issue, count in sorted(issues.items()):
            print(f"{issue}: {count}")
    else:
        print("No issues found.")

    kpis = connection.execute(
        """
        SELECT
            COUNT(*) AS orders,
            SUM(units) AS units,
            SUM(units * unit_price) AS gross_sales,
            SUM(units * unit_price * (1 - discount_pct)) AS net_sales,
            SUM(units * unit_cost) AS total_cost,
            SUM(units * unit_price * (1 - discount_pct) - units * unit_cost) AS profit
        FROM sales
        """
    ).fetchone()
    margin = kpis["profit"] / kpis["net_sales"] if kpis["net_sales"] else 0
    print("\nOVERALL KPIs")
    for label, key in (
        ("Orders", "orders"),
        ("Units", "units"),
        ("Gross sales", "gross_sales"),
        ("Net sales", "net_sales"),
        ("Cost", "total_cost"),
        ("Profit", "profit"),
    ):
        value = kpis[key]
        print(f"{label}: {value if key in ('orders', 'units') else f'${value:,.2f}'}")
    print(f"Profit margin: {margin:.1%}")

    for heading, query in (
        (
            "BY CATEGORY",
            """
            SELECT category,
                   SUM(units * unit_price * (1 - discount_pct)) AS net_sales,
                   SUM(units * unit_price * (1 - discount_pct) - units * unit_cost) AS profit
            FROM sales
            GROUP BY category
            ORDER BY net_sales DESC
            """,
        ),
        (
            "BY REGION",
            """
            SELECT region,
                   SUM(units * unit_price * (1 - discount_pct)) AS net_sales,
                   SUM(units * unit_price * (1 - discount_pct) - units * unit_cost) AS profit
            FROM sales
            GROUP BY region
            ORDER BY net_sales DESC
            """,
        ),
        (
            "BY MONTH",
            """
            SELECT substr(date, 1, 7) AS month,
                   SUM(units * unit_price * (1 - discount_pct)) AS net_sales
            FROM sales
            GROUP BY month
            ORDER BY month
            """,
        ),
    ):
        print(f"\n{heading}")
        for result in connection.execute(query):
            if heading == "BY MONTH":
                print(f"{result['month']}: net sales ${result['net_sales']:,.2f}")
            else:
                print(
                    f"{result['category'] if heading == 'BY CATEGORY' else result['region']}: "
                    f"net sales ${result['net_sales']:,.2f} | profit ${result['profit']:,.2f}"
                )

    connection.close()


if __name__ == "__main__":
    main()
