import random
import pandas as pd
from datetime import datetime, timedelta

from src.config import OUTPUT_DIR, START_DATE, MONTHS_HISTORY
from src.utils.utils import on_going_messages
from src.generate_data.generate_support_value import SEASONAL_FACTORS

#===============================
# table orders configuration
#===============================

# Sales MarkUp
MRK_MIN = 3.0
MRK_MAX = 4.0

# Annual growth rate range
GRW_MIN = 0
GRW_MAX = 0.10

# Per-importance configuration:
#   qty_min / qty_max : daily base quantity per single order line
#   daily_prob        : probability that this item is ordered on any given day
#   cust_max          : max number of customers that can order the same item in one day
#
# These parameters are calibrated so that imp_1 drives ~70 % of total volume,
# imp_2 ~15 %, imp_3 ~15 %.
IMP_CONFIG = {
    "imp_1": {"qty_min": 8,  "qty_max": 30, "daily_prob": 0.65, "cust_max": 4},
    "imp_2": {"qty_min": 3,  "qty_max": 10, "daily_prob": 0.35, "cust_max": 3},
    "imp_3": {"qty_min": 1,  "qty_max":  5, "daily_prob": 0.20, "cust_max": 2},
}


def _generate_all_days(start_date, months):
    """Return a list of every calendar day in the period [start_date, start_date + months)."""
    y = start_date.year + (start_date.month - 1 + months) // 12
    m = (start_date.month - 1 + months) % 12 + 1
    end_date = datetime(y, m, 1)

    days = []
    current = start_date
    while current < end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def generate_ordinato(materials_df, customers_df):
    """
    Genera il file Ordinato.csv con gli ordini giornalieri degli ultimi 36 mesi.

    For each material the daily demand is driven by its Importance level (see IMP_CONFIG).
    On any given day, a material is ordered only with probability daily_prob; if it is
    ordered, 1–cust_max customers are selected at random and a per-customer quantity is
    computed as:

        daily_base_qty * growth_factor * seasonal_factor * random_noise / num_customers

    where:
        growth_factor   accounts for cumulative annual growth up to that day
        seasonal_factor is driven by generate_seasonal_factor() for the current month
        random_noise    adds ±20-30 % noise

    The volume distribution across importance levels is approximately:
        imp_1 ~70 %  |  imp_2 ~15 %  |  imp_3 ~15 %

    The output is saved to OUTPUT_DIR/Ordinato.csv.

    Fields generated:
        OrderID         (str)   : Sequential unique identifier (format: ORDxxxxxx)
        OrderDate       (str)   : Order date in YYYY-MM-DD format
        RequestedDate   (str)   : Requested delivery date (7–60 days after OrderDate)
        MaterialID      (str)   : Reference to MasterMaterial
        CustomerID      (str)   : Reference to MasterCustomer
        QuantityOrdered (int)   : Units ordered by this customer on this day
        OrderValue      (float) : Revenue (QuantityOrdered * UnitCost * random markup MRK_MIN–MRK_MAX)

    Args:
        materials_df: DataFrame dei materiali (deve contenere la colonna Importance)
        customers_df: DataFrame dei clienti

    Returns:
        DataFrame con gli ordini
    """
    on_going_messages("Generating orders...")

    all_days = _generate_all_days(START_DATE, MONTHS_HISTORY)
    customer_ids = list(customers_df["CustomerID"])

    orders = []
    order_id = 1

    for _, material in materials_df.iterrows():
        material_id = material["MaterialID"]
        unit_cost   = material["UnitCost"]
        importance  = material["Importance"]
        cfg         = IMP_CONFIG[importance]

        annual_growth = random.uniform(GRW_MIN, GRW_MAX)

        for day_idx, date in enumerate(all_days):
            # Skip this day with probability (1 - daily_prob)
            if random.random() > cfg["daily_prob"]:
                continue

            growth_factor   = 1 + annual_growth * (day_idx / 365)
            seasonal_factor = SEASONAL_FACTORS[str(date.month)][0]
            random_factor   = random.uniform(0.8, 1.3)

            daily_qty = max(1, int(
                random.randint(cfg["qty_min"], cfg["qty_max"])
                * growth_factor * seasonal_factor * random_factor
            ))

            num_customers     = random.randint(1, cfg["cust_max"])
            selected_customers = random.sample(customer_ids, min(num_customers, len(customer_ids)))

            for customer_id in selected_customers:
                customer_qty = max(1, int(daily_qty / num_customers * random.uniform(0.7, 1.3)))

                requested_date = date + timedelta(days=random.randint(7, 60))
                orders.append({
                    "OrderID":         f"ORD{order_id:06d}",
                    "OrderDate":       date.strftime("%Y-%m-%d"),
                    "RequestedDate":   requested_date.strftime("%Y-%m-%d"),
                    "MaterialID":      material_id,
                    "CustomerID":      customer_id,
                    "QuantityOrdered": customer_qty,
                    "OrderValue":      round(customer_qty * unit_cost * random.uniform(MRK_MIN, MRK_MAX), 2),
                })
                order_id += 1

    df = pd.DataFrame(orders)
    df.to_csv(OUTPUT_DIR / "Ordinato.csv", index=False)
    on_going_messages(f"[OK] Generated Orders.csv - {len(df)} orders")
    print(f"[OK] Generati {len(df)} ordini")
    return df
