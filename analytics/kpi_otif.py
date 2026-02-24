"""
analytics/kpi_otif.py
---------------------
Genera due file JSON per l'analisi OTIF (On Time In Full):

  kpi_otif_by_month.json
      OTIF aggregato mensile su tutti gli ordini.
      Adatto per un grafico a linee o a barre (trend mensile).

  kpi_otif_by_customer_month.json
      OTIF disaggregato per CustomerID × mese.
      Adatto per una heatmap o per linee multiple per cliente.

Definizione OTIF:
  - On Time : ShipmentDate <= RequestedDate
              (ordini non evasi = NOT on time)
  - In Full : QuantitySold >= QuantityOrdered
              (consegne parziali o non evase = NOT in full)
  - OTIF    : On Time AND In Full

Mese di riferimento: OrderDate (mese in cui l'ordine è stato emesso).

Output:
  data_output/analytics/kpi_otif_by_month.json
  data_output/analytics/kpi_otif_by_customer_month.json

Utilizzo:
  python -m analytics.kpi_otif
"""

import json
import random
import pandas as pd
from pathlib import Path
from datetime import date

# Numero di clienti estratti casualmente per il JSON by-customer
SAMPLE_N_CUSTOMERS = 10

OUTPUT_DIR    = Path("data_output")
ANALYTICS_DIR = OUTPUT_DIR / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def _meta(description: str, tables: list[str]) -> dict:
    return {
        "description":  description,
        "tables":       tables,
        "generated_at": date.today().isoformat(),
    }


def _load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordinato  = pd.read_csv(OUTPUT_DIR / "Ordinato.csv",
                            parse_dates=["OrderDate", "RequestedDate"])
    venduto   = pd.read_csv(OUTPUT_DIR / "Venduto.csv",
                            parse_dates=["ShipmentDate"])
    customers = pd.read_csv(OUTPUT_DIR / "MasterCustomer.csv",
                            usecols=["CustomerID", "CustomerName"])
    return ordinato, venduto, customers


def _build_otif_base(ordinato: pd.DataFrame,
                     venduto: pd.DataFrame) -> pd.DataFrame:
    """
    Restituisce il DataFrame degli ordini con le colonne OTIF calcolate.

    Ogni riga è un ordine (da Ordinato). Gli ordini non evasi hanno
    ShipmentDate = NaT e QuantitySold = NaN → NOT on time, NOT in full.
    """
    # 1 ordine → al massimo 1 riga Venduto: il join è sicuro
    venduto_slim = venduto[["OrderID", "ShipmentDate", "QuantitySold"]].copy()

    df = ordinato.merge(venduto_slim, on="OrderID", how="left")

    df["is_on_time"] = (
        df["ShipmentDate"].notna() &
        (df["ShipmentDate"] <= df["RequestedDate"])
    )
    df["is_in_full"] = (
        df["QuantitySold"].notna() &
        (df["QuantitySold"] >= df["QuantityOrdered"])
    )
    df["is_otif"] = df["is_on_time"] & df["is_in_full"]

    # Mese di riferimento = mese dell'ordine
    df["month"] = df["OrderDate"].dt.to_period("M").astype(str)

    return df


def _agg_otif(df: pd.DataFrame,
              group_cols: list[str]) -> pd.DataFrame:
    """Aggrega le colonne OTIF per i group_cols specificati."""
    agg = (
        df.groupby(group_cols, as_index=False)
        .agg(
            total_orders   = ("OrderID",    "count"),
            otif_orders    = ("is_otif",    "sum"),
            on_time_orders = ("is_on_time", "sum"),
            in_full_orders = ("is_in_full", "sum"),
        )
    )
    agg["otif_rate"]     = (agg["otif_orders"]    / agg["total_orders"]).round(4)
    agg["on_time_rate"]  = (agg["on_time_orders"] / agg["total_orders"]).round(4)
    agg["in_full_rate"]  = (agg["in_full_orders"] / agg["total_orders"]).round(4)

    # Converti i conteggi in int standard per la serializzazione JSON
    for col in ["total_orders", "otif_orders", "on_time_orders", "in_full_orders"]:
        agg[col] = agg[col].astype(int)

    return agg.sort_values(group_cols).reset_index(drop=True)


def _save(payload: dict, filename: str) -> None:
    path = ANALYTICS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    n = len(payload["data"])
    print(f"[OK] {filename:<45} — {n} righe")


def main() -> None:
    ordinato, venduto, customers = _load_data()
    df = _build_otif_base(ordinato, venduto)

    # -----------------------------------------------------------------
    # KPI 1 — OTIF by month
    # -----------------------------------------------------------------
    by_month = _agg_otif(df, ["month"])
    _save(
        {
            "meta": _meta(
                "OTIF mensile aggregato — On Time In Full calcolato su tutti gli ordini. "
                "Mese di riferimento = mese dell'ordine (OrderDate). "
                "Ordini non evasi contano come NOT on time e NOT in full.",
                ["Ordinato", "Venduto"],
            ),
            "data": by_month.to_dict(orient="records"),
        },
        "kpi_otif_by_month.json",
    )

    # -----------------------------------------------------------------
    # KPI 2 — OTIF by customer × month  (campione casuale di clienti)
    # -----------------------------------------------------------------
    sampled_ids = random.sample(list(customers["CustomerID"]), SAMPLE_N_CUSTOMERS)
    customers_sample = customers[customers["CustomerID"].isin(sampled_ids)]

    df = df.merge(customers_sample, on="CustomerID", how="inner")
    by_cust = _agg_otif(df, ["month", "CustomerID", "CustomerName"])

    # Aggiungi OTIF globale del mese (benchmark di confronto per ogni cliente)
    global_otif = by_month[["month", "otif_rate"]].rename(
        columns={"otif_rate": "global_otif_rate"}
    )
    by_cust = by_cust.merge(global_otif, on="month", how="left")

    # Ranking del cliente all'interno del mese (1 = miglior OTIF del mese)
    by_cust["rank"] = (
        by_cust.groupby("month")["otif_rate"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    by_cust = by_cust.sort_values(["month", "rank"]).reset_index(drop=True)

    _save(
        {
            "meta": _meta(
                "OTIF mensile per cliente — On Time In Full disaggregato "
                "per CustomerID × mese di ordine. "
                "Include OTIF globale del mese (global_otif_rate) come benchmark "
                "e ranking del cliente nel mese (rank, 1 = miglior OTIF). "
                f"Campione casuale di {SAMPLE_N_CUSTOMERS} clienti estratti casualmente. "
                "Solo mesi con almeno un ordine sono inclusi.",
                ["Ordinato", "Venduto", "MasterCustomer"],
            ),
            "data": by_cust.to_dict(orient="records"),
        },
        "kpi_otif_by_customer_month.json",
    )


if __name__ == "__main__":
    main()
    from src.copy_to_local_directory_temp import copy_json_to_portfolio
    copy_json_to_portfolio()
