import pandas as pd
from datetime import datetime, timedelta

from src.config import OUTPUT_DIR, START_DATE, MONTHS_HISTORY
from src.utils.utils import on_going_messages

#===============================
# inventory configuration
#===============================
# Per-importance configuration:
#   initial_days      : initial stock expressed as days of average daily consumption
#   reorder_point_days: trigger a replenishment when stock drops below this many days of avg consumption
#   reorder_qty_days  : quantity to order, expressed as days of avg consumption
#
# Lead time is NOT defined here — it is read per-item from MasterMaterial.LeadTimeDays
# (set in generate_master_material.py) so that analyses such as safety stock can
# reference the exact lead time that was used during simulation.
#
# imp_1 (high importance) → large initial stock, tight reorder trigger
# imp_2 (medium)          → moderate parameters
# imp_3 (low importance)  → lean stock
INV_CONFIG = {
    "imp_1": {
        "initial_days":       60,
        "reorder_point_days": 20,
        "reorder_qty_days":   45,
    },
    "imp_2": {
        "initial_days":       45,
        "reorder_point_days": 15,
        "reorder_qty_days":   30,
    },
    "imp_3": {
        "initial_days":       30,
        "reorder_point_days": 10,
        "reorder_qty_days":   20,
    },
}

# Minimum fallback for avg daily consumption when a material has zero sales
AVG_DAILY_FALLBACK = 1


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


def generate_inventory(materials_df, sales_df):
    """
    Genera il file Inventario.csv con lo stock giornaliero per ogni materiale.

    Lo stock segue un andamento a dente di sega:
      - Le uscite giornaliere (DailyOutflow) sono ricavate da Venduto.csv
        (QuantitySold aggregato per MaterialID × ShipmentDate).
      - Le entrate (DailyInflow) sono generate da un modello a reorder point:
        quando lo stock scende sotto una soglia (reorder_point), viene piazzato
        un ordine di rifornimento che arriva dopo un lead time casuale.
      - Lo stock non scende mai sotto 0 (clamped); i giorni di stockout vengono
        loggati a console per facilitare la validazione dei parametri.

    Logica per giorno:
        ClosingStock = max(0, OpeningStock + DailyInflow - DailyOutflow)
        Se ClosingStock <= reorder_point e nessun ordine è in attesa:
            → piazza un nuovo ordine (arriverà dopo LeadTimeDays giorni, letto dal master)

    I parametri di stock (initial_days, reorder_point_days, reorder_qty_days)
    sono definiti per livello di Importance in INV_CONFIG.
    Il lead time è letto per-item da materials_df["LeadTimeDays"].

    Fields generated:
        InventoryID  (str)  : Sequential unique identifier (format: INVxxxxxxx)
        Date         (str)  : Reference date in YYYY-MM-DD format
        MaterialID   (str)  : Reference to MasterMaterial
        OpeningStock (int)  : Stock at the start of the day
        DailyInflow  (int)  : Units received from replenishment orders that day
        DailyOutflow (int)  : Units shipped (from Venduto.csv) that day
        ClosingStock (int)  : Stock at the end of the day (min 0)

    Args:
        materials_df: DataFrame dei materiali (colonne: MaterialID, Importance, LeadTimeDays)
        sales_df:     DataFrame delle vendite (colonne: MaterialID, ShipmentDate, QuantitySold)

    Returns:
        DataFrame con l'inventario giornaliero
    """
    on_going_messages("Generating inventory...")

    # --- Build outflow lookup: {material_id: {date: qty}} ---
    df_sales = sales_df.copy()
    df_sales["ShipmentDate"] = pd.to_datetime(df_sales["ShipmentDate"])

    outflow_agg = (
        df_sales
        .groupby(["MaterialID", "ShipmentDate"])["QuantitySold"]
        .sum()
        .reset_index()
    )

    outflow_dict = {}
    for _, row in outflow_agg.iterrows():
        mat  = row["MaterialID"]
        date = row["ShipmentDate"].date()
        outflow_dict.setdefault(mat, {})[date] = int(row["QuantitySold"])

    all_days   = _generate_all_days(START_DATE, MONTHS_HISTORY)
    total_days = len(all_days)

    records    = []
    inv_id     = 1
    stockout_log = {}

    for _, material in materials_df.iterrows():
        mat_id     = material["MaterialID"]
        importance = material["Importance"]
        lead_time  = int(material["LeadTimeDays"])
        cfg        = INV_CONFIG[importance]

        mat_outflows = outflow_dict.get(mat_id, {})

        # Average daily consumption over the full history window
        avg_daily = (
            sum(mat_outflows.values()) / total_days
            if total_days > 0
            else AVG_DAILY_FALLBACK
        )
        if avg_daily == 0:
            avg_daily = AVG_DAILY_FALLBACK

        initial_stock  = max(10, int(avg_daily * cfg["initial_days"]))
        reorder_point  = max(5,  int(avg_daily * cfg["reorder_point_days"]))
        reorder_qty    = max(10, int(avg_daily * cfg["reorder_qty_days"]))

        opening_stock   = initial_stock
        pending_orders  = {}   # {arrival_date (date): qty}
        stockout_days   = 0

        for day in all_days:
            day_date = day.date()

            # Receive any replenishment arriving today
            inflow  = pending_orders.pop(day_date, 0)

            # Outflow from Venduto
            outflow = mat_outflows.get(day_date, 0)

            # Closing stock — clamped to 0
            closing_raw   = opening_stock + inflow - outflow
            closing_stock = max(0, closing_raw)

            if closing_raw < 0:
                stockout_days += 1

            records.append({
                "InventoryID":  f"INV{inv_id:07d}",
                "Date":         day.strftime("%Y-%m-%d"),
                "MaterialID":   mat_id,
                "OpeningStock": opening_stock,
                "DailyInflow":  inflow,
                "DailyOutflow": outflow,
                "ClosingStock": closing_stock,
            })
            inv_id += 1

            # Place a replenishment order if below reorder point and none pending
            if closing_stock <= reorder_point and len(pending_orders) == 0:
                arrival_date = (day + timedelta(days=lead_time)).date()
                pending_orders[arrival_date] = reorder_qty

            opening_stock = closing_stock

        stockout_log[mat_id] = stockout_days

    # --- Stockout summary ---
    total_stockouts = sum(stockout_log.values())
    if total_stockouts > 0:
        on_going_messages(f"[WARN] Stockout days detected:")
        for mat_id, days in stockout_log.items():
            if days > 0:
                print(f"         {mat_id}: {days} days")
    else:
        on_going_messages("[OK] No stockout days detected")

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_DIR / "Inventario.csv", index=False)
    on_going_messages(f"[OK] Generated Inventario.csv - {len(df)} rows")
    return df
