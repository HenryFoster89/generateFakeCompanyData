import random
import pandas as pd
from datetime import datetime

from src.config import OUTPUT_DIR, START_DATE, MONTHS_HISTORY, MONTHS_FORECAST
from src.utils.utils import on_going_messages
from src.generate_data.generate_support_value import SEASONAL_FACTORS

#===============================
# forecast configuration
#===============================
# Forecast horizons to generate (months ahead).
# Generates one row per (ForecastMadeOn, MaterialID, Horizon).
HORIZONS = list(range(1, 16))   # 1 → 15 months ahead

# Noise amplitude (±%) grows linearly with the horizon:
#   noise_amp = NOISE_BASE + NOISE_SLOPE × (horizon - 1)
# Resulting MAPE targets (approximate):
#   H=1  → ±10%    H=3  → ±15%    H=6  → ±22.5%
#   H=12 → ±37.5%  H=15 → ±45%
NOISE_BASE  = 0.10   # ±10% at H=1
NOISE_SLOPE = 0.025  # +2.5 pp per additional month

# Per-material systematic bias range (stable across horizons and months).
# Negative = under-forecast; positive = over-forecast.
# Slight positive skew is realistic: forecasters tend to overestimate demand.
BIAS_MIN = -0.10
BIAS_MAX =  0.15

# Annual growth rate used to extrapolate future months (where no actuals exist).
FORECAST_GRW_MIN = 0.02
FORECAST_GRW_MAX = 0.08


def _subtract_months(dt: datetime, months: int) -> datetime:
    """Return the first day of the month that is `months` before `dt`."""
    total = dt.year * 12 + (dt.month - 1) - months
    return datetime(total // 12, total % 12 + 1, 1)


def generate_forecast(sales_df, materials_df):
    """
    Genera il file Forecast.csv con il forecast mensile della domanda per materiale.

    Per ogni materiale genera previsioni a 15 orizzonti (H=1 … H=15 mesi) per
    tutti i mesi della finestra (MONTHS_HISTORY + MONTHS_FORECAST).

    Schema della tabella (formato tall):
        ForecastID     (str)   : Identificatore univoco (formato: FCSTxxxxxxx)
        ForecastMadeOn (str)   : Mese in cui il forecast è stato prodotto (YYYY-MM)
                                 = ForecastMonth − Horizon mesi
        ForecastMonth  (str)   : Mese previsto (YYYY-MM)
        MaterialID     (str)   : Riferimento a MasterMaterial
        Horizon        (int)   : Orizzonte previsionale in mesi (1 … 15)
        ForecastQty    (int)   : Quantità prevista (min 1)
        ForecastValue  (float) : Valore previsto (ForecastQty × UnitPrice)

    Modello di errore:
        - Ogni materiale riceve un bias casuale stabile (errore sistematico).
        - Il rumore cresce linearmente con l'orizzonte:
              noise_amp = NOISE_BASE + NOISE_SLOPE × (Horizon − 1)
        - Per i mesi storici la base è la quantità effettiva (da Venduto).
        - Per i mesi futuri si usa la media storica × stagionalità × crescita
          (stesso approccio di generate_budget.py).

    Analisi di accuracy:
        Unire Forecast con Venduto su (MaterialID, ForecastMonth = YearMonth),
        filtrare sui mesi storici dove esistono le vendite reali, poi calcolare
        MAPE / MAE / Bias per ciascun orizzonte.

    Args:
        sales_df:     DataFrame Venduto (colonne: MaterialID, ShipmentDate,
                      QuantitySold, SaleValue)
        materials_df: DataFrame MasterMaterial (colonne: MaterialID, UnitPrice)

    Returns:
        DataFrame con il forecast mensile (tall format)
    """
    on_going_messages("Generating forecast...")

    # --- Build list of all months in the full window ---
    all_months = []
    current = START_DATE
    for _ in range(MONTHS_HISTORY + MONTHS_FORECAST):
        all_months.append(current)
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    # --- Aggregate actual monthly sales per material ---
    df_sales = sales_df.copy()
    df_sales["YearMonth"] = pd.to_datetime(df_sales["ShipmentDate"]).dt.to_period("M")

    actual_agg = (
        df_sales
        .groupby(["MaterialID", "YearMonth"])["QuantitySold"]
        .sum()
        .reset_index()
        .rename(columns={"QuantitySold": "ActualQty"})
    )

    # Actual lookup: {mat_id: {ym_str: qty}}
    actual_dict: dict[str, dict[str, int]] = {}
    for _, row in actual_agg.iterrows():
        mat = row["MaterialID"]
        ym  = str(row["YearMonth"])   # e.g. "2023-01"
        actual_dict.setdefault(mat, {})[ym] = int(row["ActualQty"])

    # Historical monthly avg per material (used to extrapolate future months)
    avg_lookup: dict[str, float] = (
        actual_agg
        .groupby("MaterialID")["ActualQty"]
        .mean()
        .to_dict()
    )

    # Unit price lookup
    price_lookup: dict[str, float] = (
        materials_df.set_index("MaterialID")["UnitPrice"].to_dict()
    )

    records    = []
    forecast_id = 1

    for _, material in materials_df.iterrows():
        mat_id     = material["MaterialID"]
        unit_price = price_lookup.get(mat_id, 0.0)

        # Per-material stable bias and growth rate (sampled once per material)
        bias          = random.uniform(BIAS_MIN, BIAS_MAX)
        annual_growth = random.uniform(FORECAST_GRW_MIN, FORECAST_GRW_MAX)
        avg_qty       = avg_lookup.get(mat_id, 1.0)

        for month_idx, date in enumerate(all_months):
            ym_str    = date.strftime("%Y-%m")
            is_future = month_idx >= MONTHS_HISTORY

            # Base quantity: actual for historical months, extrapolated for future
            if not is_future and ym_str in actual_dict.get(mat_id, {}):
                base_qty = actual_dict[mat_id][ym_str]
            else:
                seasonal_factor = SEASONAL_FACTORS[str(date.month)][0]
                growth_factor   = 1 + annual_growth * (month_idx / 12)
                base_qty        = avg_qty * seasonal_factor * growth_factor

            for horizon in HORIZONS:
                noise_amp      = NOISE_BASE + NOISE_SLOPE * (horizon - 1)
                noise          = random.uniform(-noise_amp, noise_amp)
                multiplier     = 1 + bias + noise

                fcst_qty       = max(1, int(base_qty * multiplier))
                fcst_value     = round(fcst_qty * unit_price, 2)
                made_on_date   = _subtract_months(date, horizon)

                records.append({
                    "ForecastID":     f"FCST{forecast_id:07d}",
                    "ForecastMadeOn": made_on_date.strftime("%Y-%m"),
                    "ForecastMonth":  ym_str,
                    "MaterialID":     mat_id,
                    "Horizon":        horizon,
                    "ForecastQty":    fcst_qty,
                    "ForecastValue":  fcst_value,
                })
                forecast_id += 1

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_DIR / "Forecast.csv", index=False)
    on_going_messages(f"[OK] Generated Forecast.csv - {len(df)} rows")
    return df
