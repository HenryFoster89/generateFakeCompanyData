"""
testing_inventory.py
--------------------
Validation script for Inventario.csv.

For each material, plots Date vs ClosingStock and saves the image to
img/testing_inventory/<MaterialID>.png.

Also plots the total inventory (sum of all materials) and saves it to
img/testing_inventory/TOTAL.png.

Run from the project root:
    python testing_inventory.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CSV_PATH  = Path("data_output/Inventario.csv")
OUT_DIR   = Path("img/testing_inventory")
FIG_W     = 16
FIG_H     = 5

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Loading Inventario.csv...")
df = pd.read_csv(CSV_PATH, parse_dates=["Date"])
df = df.sort_values(["MaterialID", "Date"])
print(f"  {len(df):,} rows | {df['MaterialID'].nunique()} materials | "
      f"{df['Date'].min().date()} → {df['Date'].max().date()}")

OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helper: format x-axis with monthly ticks
# ---------------------------------------------------------------------------
def _fmt_xaxis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")


# ---------------------------------------------------------------------------
# Plot per material
# ---------------------------------------------------------------------------
materials = df["MaterialID"].unique()

for mat_id in materials:
    dm = df[df["MaterialID"] == mat_id].copy()

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

    # ClosingStock area + line
    ax.fill_between(dm["Date"], dm["ClosingStock"], alpha=0.15, color="steelblue")
    ax.plot(dm["Date"], dm["ClosingStock"], color="steelblue", linewidth=1.2,
            label="Closing Stock")

    # Mark inflow events (replenishments) as vertical green lines
    inflow_days = dm[dm["DailyInflow"] > 0]
    for _, row in inflow_days.iterrows():
        ax.axvline(row["Date"], color="green", alpha=0.5, linewidth=0.8, linestyle="--")

    # Highlight stockout days (ClosingStock == 0 and DailyOutflow > 0) in red
    stockout = dm[(dm["ClosingStock"] == 0) & (dm["DailyOutflow"] > 0)]
    if not stockout.empty:
        ax.scatter(stockout["Date"], stockout["ClosingStock"],
                   color="red", zorder=5, s=20, label=f"Stockout ({len(stockout)} days)")

    ax.set_title(f"Inventory — {mat_id}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Quantity")
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    _fmt_xaxis(ax)

    plt.tight_layout()
    out_path = OUT_DIR / f"{mat_id}.png"
    plt.savefig(out_path, dpi=100)
    plt.close()
    print(f"  [OK] {out_path}")


# ---------------------------------------------------------------------------
# Plot total inventory (sum of all materials)
# ---------------------------------------------------------------------------
total = (
    df.groupby("Date")
    .agg(
        TotalClosing=("ClosingStock", "sum"),
        TotalInflow=("DailyInflow", "sum"),
        TotalOutflow=("DailyOutflow", "sum"),
    )
    .reset_index()
)

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

ax.fill_between(total["Date"], total["TotalClosing"], alpha=0.15, color="darkorange")
ax.plot(total["Date"], total["TotalClosing"], color="darkorange", linewidth=1.4,
        label="Total Closing Stock")

# Mark days with inflows
inflow_total = total[total["TotalInflow"] > 0]
for _, row in inflow_total.iterrows():
    ax.axvline(row["Date"], color="green", alpha=0.3, linewidth=0.7, linestyle="--")

ax.set_title("Total Inventory — All Materials", fontsize=13, fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("Quantity")
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle="--", alpha=0.4)
_fmt_xaxis(ax)

plt.tight_layout()
out_path = OUT_DIR / "TOTAL.png"
plt.savefig(out_path, dpi=100)
plt.close()
print(f"  [OK] {out_path}")

print(f"\nDone. All plots saved in '{OUT_DIR}/'")
