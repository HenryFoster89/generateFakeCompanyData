import random
import pandas as pd
from datetime import datetime

from src.config import OUTPUT_DIR, START_DATE, MONTHS_HISTORY, MONTHS_FORECAST
from src.utils.utils import on_going_messages
from src.generate_data.generate_orders import SEASONAL_FACTORS

#===============================
# budget configuration
#===============================
# Monthly buffer range applied to the projected qty/value (±%)
BUFFER_MIN = -0.15
BUFFER_MAX =  0.15

# Annual growth rate for the forward projection
BUDGET_GRW_MIN = 0.02
BUDGET_GRW_MAX = 0.08


def generate_budget(orders_df):
    """
    Genera il file Budget.csv con il budget mensile per materiale.

    Aggrega lo storico degli ordini per MaterialID × Mese, calcola la media
    mensile per ogni materiale e genera il budget per l'intero arco temporale
    (MONTHS_HISTORY + MONTHS_FORECAST mesi a partire da START_DATE) applicando:
      - seasonal_factor  : fattore stagionale del mese
      - growth_factor    : crescita annua lineare (campionata per materiale)
      - buffer_factor    : buffer casuale mensile in [1+BUFFER_MIN, 1+BUFFER_MAX]

    Il budget copre lo stesso intervallo di ordini e vendite più 12 mesi
    di forecast (START_DATE → START_DATE + MONTHS_HISTORY + MONTHS_FORECAST).

    Fields generated:
        BudgetID     (str)   : Sequential unique identifier (format: BDGxxxxxx)
        BudgetMonth  (str)   : Budget month in YYYY-MM format
        MaterialID   (str)   : Reference to MasterMaterial
        BudgetQty    (int)   : Planned quantity
        BudgetValue  (float) : Planned revenue

    Args:
        orders_df: DataFrame degli ordini (deve contenere le colonne di Ordinato.csv)

    Returns:
        DataFrame con il budget
    """
    on_going_messages("Generating budget...")

    # Budget covers the full historical window + forecast
    # Start: same as orders/sales (START_DATE)
    # End:   MONTHS_HISTORY + MONTHS_FORECAST months later

    # Build list of budget dates
    proj_dates = []
    current = START_DATE
    for _ in range(MONTHS_HISTORY + MONTHS_FORECAST):
        proj_dates.append(current)
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    # Average monthly qty and value per MaterialID over the historical period
    df_hist = orders_df.copy()
    df_hist["YearMonth"] = pd.to_datetime(df_hist["OrderDate"]).dt.to_period("M")

    monthly_agg = (
        df_hist
        .groupby(["MaterialID", "YearMonth"])
        .agg(TotalQty=("QuantityOrdered", "sum"), TotalValue=("OrderValue", "sum"))
        .reset_index()
    )
    avg_per_material = (
        monthly_agg
        .groupby("MaterialID")
        .agg(AvgQty=("TotalQty", "mean"), AvgValue=("TotalValue", "mean"))
        .reset_index()
    )

    budget   = []
    budget_id = 1

    for _, mat in avg_per_material.iterrows():
        material_id = mat["MaterialID"]
        avg_qty     = mat["AvgQty"]
        avg_value   = mat["AvgValue"]

        annual_growth = random.uniform(BUDGET_GRW_MIN, BUDGET_GRW_MAX)

        for month_idx, date in enumerate(proj_dates):
            growth_factor   = 1 + annual_growth * (month_idx / 12)
            seasonal_factor = SEASONAL_FACTORS[str(date.month)][0]
            buffer_factor   = random.uniform(1 + BUFFER_MIN, 1 + BUFFER_MAX)

            combined = growth_factor * seasonal_factor * buffer_factor

            budget.append({
                "BudgetID":    f"BDG{budget_id:06d}",
                "BudgetMonth": date.strftime("%Y-%m"),
                "MaterialID":  material_id,
                "BudgetQty":   max(1, int(avg_qty * combined)),
                "BudgetValue": round(avg_value * combined, 2),
            })
            budget_id += 1

    df = pd.DataFrame(budget)
    df.to_csv(OUTPUT_DIR / "Budget.csv", index=False)
    on_going_messages(f"[OK] Generated Budget.csv - {len(df)} rows")
    print(f"[OK] Generati {len(df)} righe budget")
    return df
