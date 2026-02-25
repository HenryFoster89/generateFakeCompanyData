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

import sys
import json
import random
import pandas as pd
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.copy_to_local_directory_temp import copy_json_to_portfolio

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

# Numero di clienti estratti casualmente per il JSON by-customer.
# Tenuto basso per non appesantire il JSON — cambia se vuoi più clienti.
SAMPLE_N_CUSTOMERS = 10

# Cartella radice dei CSV generati da generate_fake_data.py
OUTPUT_DIR    = Path("data_output")

# Sottocartella dove vengono scritti i JSON di analytics
ANALYTICS_DIR = OUTPUT_DIR / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _meta(description: str, tables: list[str]) -> dict:
    """
    Costruisce il blocco 'meta' da inserire in testa ad ogni JSON.

    Contiene:
      - description : testo libero che spiega il KPI
      - tables      : lista delle tabelle sorgente usate per il calcolo
      - generated_at: data di generazione (ISO 8601, solo giorno)
    """
    return {
        "description":  description,
        "tables":       tables,
        "generated_at": date.today().isoformat(),
    }


def _load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Legge i CSV necessari da OUTPUT_DIR e li restituisce come DataFrame.

    Tabelle caricate:
      - Ordinato.csv  : tutti gli ordini (1 riga = 1 ordine)
      - Venduto.csv   : tutte le spedizioni/vendite (1 riga = 1 riga di venduto)
      - MasterCustomer.csv : anagrafica clienti (solo CustomerID e CustomerName)

    Le date vengono parsate direttamente in datetime per facilitare i confronti.
    """
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
    Costruisce il DataFrame base con le colonne OTIF calcolate riga per riga.

    Logica:
      1. LEFT JOIN tra Ordinato e Venduto su OrderID.
         - Gli ordini non ancora evasi avranno ShipmentDate = NaT
           e QuantitySold = NaN dopo il join.
      2. is_on_time = True solo se ShipmentDate non è nulla
                      E ShipmentDate <= RequestedDate.
         - Ordini non evasi → NOT on time (NaT non passa il confronto).
      3. is_in_full = True solo se QuantitySold non è nulla
                      E QuantitySold >= QuantityOrdered.
         - Ordini non evasi o consegne parziali → NOT in full.
      4. is_otif = is_on_time AND is_in_full.
      5. month   = periodo mensile dell'OrderDate (es. "2024-03").
                   È il mese di riferimento usato in tutte le aggregazioni.

    Restituisce:
      DataFrame con tutte le colonne di Ordinato + ShipmentDate,
      QuantitySold, is_on_time, is_in_full, is_otif, month.
    """
    # Prendiamo solo le colonne di Venduto che ci servono per il calcolo OTIF
    #venduto_slim = venduto[["OrderID", "ShipmentDate", "QuantitySold"]].copy()
    cols_venduto = ["OrderID", "ShipmentDate", "QuantitySold"]
    # LEFT JOIN: manteniamo tutti gli ordini, anche quelli non evasi
    df = ordinato.merge(venduto[cols_venduto], 
                        on="OrderID", 
                        how="left")

    # On Time: spedizione avvenuta E non in ritardo rispetto alla data richiesta
    df["onTime"] = (
        df["ShipmentDate"].notna() &
        (df["ShipmentDate"] <= df["RequestedDate"])
    )

    # In Full: quantità consegnata >= quantità ordinata (nessuna consegna parziale)
    df["inFull"] = (
        df["QuantitySold"].notna() &
        (df["QuantitySold"] >= df["QuantityOrdered"])
    )

    # OTIF: entrambe le condizioni soddisfatte contemporaneamente
    df["is_otif"] = df["onTime"] & df["inFull"]

    # Mese dell'ordine come stringa "YYYY-MM" per raggruppamenti e ordinamenti
    df["month"] = df["RequestedDate"].dt.to_period("M").astype(str)
    
    print("1 - BREAKPOINT")
    print(df)
    return df


def _agg_otif(df: pd.DataFrame,
              group_cols: list[str]) -> pd.DataFrame:
    """
    Aggrega le metriche OTIF per i group_cols specificati.

    Colonne calcolate per ogni gruppo:
      - total_orders   : numero totale di ordini nel gruppo
      - otif_orders    : ordini che soddisfano sia On Time che In Full
      - on_time_orders : ordini consegnati in tempo (indipendentemente dal full)
      - in_full_orders : ordini consegnati completi (indipendentemente dal tempo)
      - otif_rate      : otif_orders / total_orders  (0.0 – 1.0, 4 decimali)
      - on_time_rate   : on_time_orders / total_orders
      - in_full_rate   : in_full_orders / total_orders

    I conteggi vengono castati a int standard per evitare problemi
    di serializzazione JSON con numpy int64.
    """
    agg = (
        df.groupby(group_cols, as_index=False)
        .agg(
            total_orders   = ("OrderID",  "count"),
            otif_orders    = ("is_otif",  "sum"),
            on_time_orders = ("onTime",   "sum"),
            in_full_orders = ("inFull",   "sum"),
        )
    )
    print("BREAKPOINT")
    print(agg)
    print("END BREAKPOINT")

    # Calcolo dei rate (percentuali in formato decimale)
    agg["otif_rate"]     = (agg["otif_orders"]    / agg["total_orders"]).round(4)
    agg["on_time_rate"]  = (agg["on_time_orders"] / agg["total_orders"]).round(4)
    agg["in_full_rate"]  = (agg["in_full_orders"] / agg["total_orders"]).round(4)

    # Conversione a int nativo Python per la serializzazione JSON
    for col in ["total_orders", "otif_orders", "on_time_orders", "in_full_orders"]:
        agg[col] = agg[col].astype(int)

    return agg.sort_values(group_cols).reset_index(drop=True)


def _save(payload: dict, filename: str) -> None:
    """
    Serializza il payload come JSON e lo scrive in ANALYTICS_DIR.

    Il payload deve avere la struttura:
      { "meta": {...}, "data": [...] }

    Stampa a console il nome del file e il numero di righe nel campo 'data'.
    """
    path = ANALYTICS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    n = len(payload["data"])
    print(f"[OK] {filename:<45} — {n} righe")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Load ordinato, venduto, MasterCustomer from csv files
    ordinato, venduto, customers = _load_data()

    # OTIF calculation is returned to df
    df = _build_otif_base(ordinato, venduto)

    # -----------------------------------------------------------------
    # KPI 1 — OTIF aggregato per mese (tutti i clienti)
    # -----------------------------------------------------------------
    # Raggruppiamo solo per mese: 1 riga = 1 mese, con i totali globali.
    # Questo JSON è pensato per grafici a linee o a barre sul trend mensile.
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
    # KPI 2 — OTIF per cliente × mese (campione casuale di clienti)
    # -----------------------------------------------------------------
    # Estraiamo casualmente SAMPLE_N_CUSTOMERS clienti per contenere
    # le dimensioni del JSON (con tutti i clienti sarebbe troppo grande).
    sampled_ids      = random.sample(list(customers["CustomerID"]), SAMPLE_N_CUSTOMERS)
    customers_sample = customers[customers["CustomerID"].isin(sampled_ids)]

    # INNER JOIN: teniamo solo gli ordini dei clienti campionati
    df = df.merge(customers_sample, on="CustomerID", how="inner")

    # Aggregazione per mese × cliente
    by_cust = _agg_otif(df, ["month", "CustomerID", "CustomerName"])

    # Aggiungiamo l'OTIF globale del mese come benchmark di confronto:
    # permette di vedere se un cliente è sopra o sotto la media mensile.
    global_otif = by_month[["month", "otif_rate"]].rename(
        columns={"otif_rate": "global_otif_rate"}
    )
    by_cust = by_cust.merge(global_otif, on="month", how="left")

    # Ranking del cliente all'interno del mese:
    # rank=1 → miglior OTIF del mese, rank=N → peggiore.
    # Utile per heatmap o classifiche dinamiche in dashboard.
    by_cust["rank"] = (
        by_cust.groupby("month")["otif_rate"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    # Ordine finale: prima per mese, poi per ranking (migliori in cima)
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
    copy_json_to_portfolio()
