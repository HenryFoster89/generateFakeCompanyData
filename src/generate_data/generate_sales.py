import random
import pandas as pd
from datetime import datetime, timedelta

from src.config import OUTPUT_DIR
from src.utils.utils import on_going_messages

#===============================
# table sales configuration
#===============================
# Probability that an order generates at least a partial sale
FULFILLMENT_RATE = 0.95

# Among fulfilled orders, probability that fulfillment is partial (qty < ordered)
PARTIAL_RATE = 0.17

# Minimum fulfillment ratio for partial deliveries (e.g. 0.30 = at least 30% delivered)
MIN_PARTIAL_RATIO = 0.30

# Probability that a shipment is on time (ShipmentDate <= RequestedDate)
ON_TIME_RATE = 0.85

# Shipment date offset relative to RequestedDate (days):
#   negative = early delivery, positive = late delivery
SHIP_EARLY_MAX = 5
SHIP_LATE_MAX  = 10


def generate_sales(orders_df):
    """
    Genera il file Venduto.csv a partire dagli ordini (Ordinato.csv).

    Not every order is fulfilled: each order has a FULFILLMENT_RATE probability of
    generating a sale record.  Among fulfilled orders, PARTIAL_RATE have a
    QuantitySold strictly less than QuantityOrdered (partial delivery).
    The SaleValue is proportionally rescaled from OrderValue to preserve
    the same per-unit price.

    Fields generated:
        SaleID          (str)   : Sequential unique identifier (format: SALExxxxxx)
        OrderID         (str)   : Reference to the originating order in Ordinato.csv
        OrderDate       (str)   : Order creation date (copied from the order)
        ShipmentDate    (str)   : Actual shipment date (RequestedDate ± a few days)
        MaterialID      (str)   : Same as in the order
        CustomerID      (str)   : Same as in the order
        QuantityOrdered (int)   : Original quantity from the order (reference)
        QuantitySold    (int)   : Actual quantity delivered (≤ QuantityOrdered)
        SaleValue       (float) : Revenue (OrderValue scaled by QuantitySold / QuantityOrdered)

    Args:
        orders_df: DataFrame degli ordini (deve contenere le colonne di Ordinato.csv)

    Returns:
        DataFrame con le vendite
    """
    on_going_messages("Generating sales...")

    sales   = []
    sale_id = 1

    for _, order in orders_df.iterrows():
        # Skip orders that are never fulfilled
        if random.random() > FULFILLMENT_RATE:
            continue

        qty_ordered = order["QuantityOrdered"]

        # Determine actual quantity sold
        if random.random() < PARTIAL_RATE:
            # Partial delivery: between MIN_PARTIAL_RATIO and 99 % of ordered qty
            partial_ratio = random.uniform(MIN_PARTIAL_RATIO, 0.99)
            qty_sold = max(1, int(qty_ordered * partial_ratio))
        else:
            # Full delivery
            qty_sold = qty_ordered

        # SaleValue proportional to OrderValue (same unit price)
        unit_value = order["OrderValue"] / qty_ordered
        sale_value = round(unit_value * qty_sold, 2)

        # ShipmentDate: actual delivery around RequestedDate
        requested_date = datetime.strptime(order["RequestedDate"], "%Y-%m-%d")
        if random.random() < ON_TIME_RATE:
            offset_days = random.randint(-SHIP_EARLY_MAX, 0)   # early or on time
        else:
            offset_days = random.randint(1, SHIP_LATE_MAX)     # late
        shipment_date  = requested_date + timedelta(days=offset_days)

        sales.append({
            "SaleID":          f"SALE{sale_id:06d}",
            "OrderID":         order["OrderID"],
            "OrderDate":       order["OrderDate"],
            "ShipmentDate":    shipment_date.strftime("%Y-%m-%d"),
            "MaterialID":      order["MaterialID"],
            "CustomerID":      order["CustomerID"],
            "QuantityOrdered": qty_ordered,
            "QuantitySold":    qty_sold,
            "SaleValue":       sale_value,
        })
        sale_id += 1

    df = pd.DataFrame(sales)
    df.to_csv(OUTPUT_DIR / "Venduto.csv", index=False)
    on_going_messages(f"[OK] Generated Venduto.csv - {len(df)} sales")
    print(f"[OK] Generate {len(df)} vendite")
    return df
