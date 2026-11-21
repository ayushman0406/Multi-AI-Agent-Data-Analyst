"""Generate samples/retail_orders.csv (synthetic, deterministic). Run: python samples/make_retail.py"""

from pathlib import Path

import numpy as np
import pandas as pd

N = 3000
OUT = Path(__file__).resolve().parent / "retail_orders.csv"


def make() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    start, end = np.datetime64("2025-01-01"), np.datetime64("2026-06-30")
    days = int((end - start).astype(int)) + 1
    order_date = start + rng.integers(0, days, N).astype("timedelta64[D]")

    regions = np.array(["North", "South", "East", "West"])
    region = rng.choice(regions, N, p=[0.27, 0.24, 0.25, 0.24])

    categories = np.array(["Electronics", "Furniture", "Grocery", "Apparel", "Sports"])
    category = rng.choice(categories, N, p=[0.18, 0.12, 0.32, 0.23, 0.15])
    base_price = {"Electronics": 180.0, "Furniture": 260.0, "Grocery": 9.0, "Apparel": 38.0, "Sports": 55.0}
    unit_price = np.array([base_price[c] for c in category]) * rng.lognormal(0.0, 0.35, N)

    units = rng.integers(1, 13, N)  # 1..12

    # discounts: mostly modest, West runs heavier promotions
    discount = rng.beta(1.6, 9.0, N) * 0.45
    discount = np.where(region == "West", discount + rng.uniform(0.05, 0.12, N), discount)
    discount = np.clip(discount, 0.0, 0.30)

    customer_id = rng.integers(1, 401, N)
    returned = rng.random(N) < 0.06

    df = pd.DataFrame({
        "order_id": np.arange(100001, 100001 + N),
        "order_date": pd.to_datetime(order_date).strftime("%Y-%m-%d"),
        "region": region,
        "category": category,
        "units": units,
        "unit_price": np.round(unit_price, 2),
        "discount": np.round(discount, 3),
        "customer_id": [f"C{c:04d}" for c in customer_id],
        "returned": returned,
    })
    df = df.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    df["order_id"] = np.arange(100001, 100001 + N)
    df["revenue"] = np.round(df["units"] * df["unit_price"] * (1 - df["discount"]), 2)
    return df


if __name__ == "__main__":
    frame = make()
    frame.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(frame)} rows)")
    print(frame.groupby("region")["discount"].mean().round(4))
