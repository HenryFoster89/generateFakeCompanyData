import random
import pandas as pd
from datetime import datetime

from src.config import START_DATE, MONTHS_HISTORY, OUTPUT_DIR
from src.utils.utils import on_going_messages
from src.generate_data.generate_support_value import generate_date_range, generate_seasonal_factor

def generate_ordinato(materials_df, customers_df):
    """
    Genera il file Ordinato.csv con gli ordini degli ultimi 36 mesi.

    Args:
        materials_df: DataFrame dei materiali
        customers_df: DataFrame dei clienti

    Returns:
        DataFrame con gli ordini
    """
    on_going_messages("Generating orders...")

    # Date degli ultimi 36 mesi
    dates = generate_date_range(START_DATE, MONTHS_HISTORY)

    orders = []
    order_id = 1

    # Per ogni materiale
    for _, material in materials_df.iterrows():
        material_id = material["MaterialID"]
        unit_cost = material["UnitCost"]

        # Quantità base mensile (varia per materiale)
        base_quantity = random.randint(100, 1000)

        # Trend di crescita annuale (0-10%)
        annual_growth = random.uniform(0, 0.10)

        # Per ogni mese
        for month_idx, date in enumerate(dates):
            month = date.month

            # Calcolare fattore di crescita
            growth_factor = 1 + (annual_growth * (month_idx / 12))

            # Applicare stagionalità
            seasonal_factor = generate_seasonal_factor(str(month))

            # Variabilità casuale (-20% +30%)
            random_factor = random.uniform(0.8, 1.3)

            # Quantità finale
            quantity = int(base_quantity * growth_factor * seasonal_factor * random_factor)

            # Alcuni clienti ordinano questo materiale
            num_orders_this_month = random.randint(3, 8)
            selected_customers = random.sample(list(customers_df["CustomerID"]), num_orders_this_month)

            for customer_id in selected_customers:
                # Distribuire la quantità tra i clienti
                customer_quantity = int(quantity / num_orders_this_month * random.uniform(0.7, 1.3))

                order = {
                    "Date": date.strftime("%Y-%m-%d"),
                    "MaterialID": material_id,
                    "CustomerID": customer_id,
                    "QuantityOrdered": customer_quantity,
                    "OrderValue": round(customer_quantity * unit_cost * random.uniform(1.2, 1.5), 2),  # Markup
                    "OrderID": f"ORD{order_id:06d}"
                }
                orders.append(order)
                order_id += 1

    df = pd.DataFrame(orders)
    df.to_csv(OUTPUT_DIR / "Ordinato.csv", index=False)
    on_going_messages(f"[OK] Generated Orders.csv - {len(df)} orders")
    print(f"[OK] Generati {len(df)} ordini")
    return df