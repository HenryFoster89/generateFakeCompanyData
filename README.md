# Goal

Create synthetic data of a pharmaceutical company for analytics and BI use cases.

---

# Project structure

```
src/
├── config.py                        # Global constants (paths, dates)
├── generate_data/
│   ├── generate_master_material.py  # Anagrafica materiali
│   ├── generate_master_customer.py  # Anagrafica clienti
│   ├── generate_orders.py           # Ordinato giornaliero
│   ├── generate_sales.py            # Venduto (da ordini)
│   ├── generate_budget.py           # Budget mensile per materiale
│   ├── generate_inventory.py        # Inventario giornaliero per materiale
│   └── generate_support_value.py    # Utility condivise (SEASONAL_FACTORS)
└── generate_sql_lite_db/
    ├── schema.py                    # Registro esplicito tabelle/tipi SQLite
    └── load_to_db.py                # Caricamento CSV → SQLite

config/
└── seasonal_pattern.json            # Fattori stagionali mensili (personalizzabili)

data_output/                         # Generato a runtime
├── MasterMaterial.csv
├── MasterCustomer.csv
├── Ordinato.csv
├── Venduto.csv
├── Budget.csv
├── Inventario.csv
└── company_data.db                  # SQLite DB (ricreato ad ogni run)
```

---

# Output

After running the pipeline, the following files are available in `data_output/`:

| File | Descrizione |
|------|-------------|
| `MasterMaterial.csv` | Anagrafica materiali |
| `MasterCustomer.csv` | Anagrafica clienti |
| `Ordinato.csv` | Ordini giornalieri (36 mesi) |
| `Venduto.csv` | Vendite consuntivate |
| `Budget.csv` | Budget mensile per materiale (storico + forecast 12 mesi) |
| `Inventario.csv` | Inventario giornaliero per materiale (modello reorder point) |
| `company_data.db` | SQLite DB con tutte le tabelle sopra |

---

# Output description

## MasterMaterial.csv

| Column | Type | Description |
|--------|------|-------------|
| MaterialID | String | Identificatore univoco (formato: MATxxx) |
| MaterialName | String | Nome sintetico del farmaco |
| Category | String | Famiglia terapeutica (Antibiotici, Analgesici, Cardiovascolari, …) |
| UnitOfMeasure | String | Unità di confezionamento (Scatole, Flaconi, Blister, Confezioni) |
| UnitCost | Float | Costo di produzione unitario |
| UnitPrice | Float | Prezzo di vendita (UnitCost × un unico markup casuale applicato a tutti) |
| Importance | String | Livello di importanza: `imp_1` (~50 %), `imp_2` (~25 %), `imp_3` (~25 %) |
| LeadTimeDays | Integer | Lead time nominale di approvvigionamento (**giorni lavorativi**), campionato per item dal range del suo livello di importanza |

## MasterCustomer.csv

| Column | Type | Description |
|--------|------|-------------|
| CustomerID | String | Identificatore univoco (formato: CUSTxxx) |
| CustomerName | String | Nome sintetico del cliente |
| CustomerType | String | Tipo di cliente (Ospedale, Farmacia, Grossista, ASL) |
| Region | String | Regione amministrativa italiana |
| PaymentTerms | Integer | Giorni di dilazione pagamento (30, 60, 90, 120) |

## Ordinato.csv

Granularità **giornaliera**. Non tutti gli item vengono ordinati ogni giorno: la probabilità di ordine dipende dal livello di importanza dell'item (vedi tabella sotto).

La distribuzione del volume ordinato è calibrata su:
- `imp_1` → ~70 % del volume totale
- `imp_2` → ~15 % del volume totale
- `imp_3` → ~15 % del volume totale

| Column | Type | Description |
|--------|------|-------------|
| OrderID | String | Identificatore univoco (formato: ORDxxxxxx) |
| OrderDate | String | Data dell'ordine (YYYY-MM-DD) |
| RequestedDate | String | Data di consegna richiesta (7–60 giorni dopo OrderDate) |
| MaterialID | String | Riferimento a MasterMaterial |
| CustomerID | String | Riferimento a MasterCustomer |
| QuantityOrdered | Integer | Quantità ordinata dal cliente in quel giorno |
| OrderValue | Float | Valore ordine (QuantityOrdered × UnitCost × markup casuale) |

**Parametri per livello di importanza (`IMP_CONFIG` in `generate_orders.py`):**

| Livello | qty_min | qty_max | daily_prob | cust_max |
|---------|---------|---------|-----------|----------|
| imp_1   | 8       | 30      | 65 %      | 4        |
| imp_2   | 3       | 10      | 35 %      | 3        |
| imp_3   | 1       | 5       | 20 %      | 2        |

## Venduto.csv

Generato a partire da `Ordinato.csv`. Non tutti gli ordini vengono evasi (tasso di fulfillment ~85 %); tra gli evasi, ~20 % è una consegna parziale.

| Column | Type | Description |
|--------|------|-------------|
| SaleID | String | Identificatore univoco (formato: SALExxxxxx) |
| OrderID | String | Riferimento all'ordine originante |
| OrderDate | String | Data dell'ordine (YYYY-MM-DD) |
| ShipmentDate | String | Data di spedizione effettiva (RequestedDate ± alcuni giorni) |
| MaterialID | String | Riferimento a MasterMaterial |
| CustomerID | String | Riferimento a MasterCustomer |
| QuantityOrdered | Integer | Quantità ordinata originale (riferimento) |
| QuantitySold | Integer | Quantità effettivamente consegnata (≤ QuantityOrdered) |
| SaleValue | Float | Ricavo (OrderValue scalato proporzionalmente) |

## Budget.csv

Granularità **mensile**. Copre l'intero storico (36 mesi) più 12 mesi di forecast. Calcolato aggregando lo storico degli ordini per materiale e proiettandolo con crescita annua e stagionalità.

| Column | Type | Description |
|--------|------|-------------|
| BudgetID | String | Identificatore univoco (formato: BDGxxxxxx) |
| BudgetMonth | String | Mese di budget (YYYY-MM) |
| MaterialID | String | Riferimento a MasterMaterial |
| BudgetQty | Integer | Quantità pianificata |
| BudgetValue | Float | Valore pianificato |

## Inventario.csv

Granularità **giornaliera per materiale**. Modella lo stock con un approccio a **reorder point**: quando lo stock scende sotto la soglia, viene piazzato un ordine di rifornimento che arriva dopo `LeadTimeDays` giorni lavorativi. Le uscite giornaliere sono ricavate direttamente da `Venduto.csv`.

L'andamento risultante è a **dente di sega**: lo stock decresce gradualmente per effetto delle vendite, poi risale bruscamente all'arrivo del rifornimento.

| Column | Type | Description |
|--------|------|-------------|
| InventoryID | String | Identificatore univoco (formato: INVxxxxxxx) |
| Date | String | Data di riferimento (YYYY-MM-DD) |
| MaterialID | String | Riferimento a MasterMaterial |
| OpeningStock | Integer | Stock a inizio giornata |
| DailyInflow | Integer | Unità ricevute da rifornimento in quel giorno |
| DailyOutflow | Integer | Unità spedite (da Venduto.csv) in quel giorno |
| ClosingStock | Integer | Stock a fine giornata — minimo 0 (giorni di stockout sono loggati a console) |

---

# SQLite Database

Il file `data_output/company_data.db` contiene tutte le tabelle sopra in un unico database SQLite, ricreato da zero ad ogni run.

Per aggiungere una nuova tabella al DB è sufficiente aggiungere una voce in `src/generate_sql_lite_db/schema.py` — nessun'altra modifica è necessaria.

```python
# Esempio di utilizzo
from src.generate_sql_lite_db.load_to_db import load_to_db
load_to_db()
```

---

# Configuration

Il pattern stagionale usato per modulare i volumi degli ordini è personalizzabile modificando:

```
config/seasonal_pattern.json
```

---

# Parametri

Ogni file `generate_*.py` espone costanti configurabili nella sezione iniziale. I parametri globali sono in `src/config.py`.

## `src/config.py` — parametri globali

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `START_DATE` | `2023-01-01` | Data di inizio della finestra temporale usata da ordini, vendite e budget |
| `MONTHS_HISTORY` | `36` | Mesi di storico da generare |
| `MONTHS_FORECAST` | `12` | Mesi di forecast aggiuntivi (solo Budget) |
| `OUTPUT_DIR` | `data_output/` | Cartella di output per tutti i CSV e il DB |
| `SEASONAL_PATTERN_PATH` | `config/seasonal_pattern.json` | Percorso del file JSON con i fattori stagionali mensili |
| `DB_PATH` | `data_output/company_data.db` | Percorso del database SQLite |

## `generate_master_material.py` — anagrafica materiali

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `NUM_MATERIALS` | `5` | Numero di materiali (SKU) da generare |
| `PRODUCT_FAMILY` | lista 8 elementi | Famiglie terapeutiche assegnabili a ciascun materiale |
| `UNITS` | `[Scatole, Flaconi, Blister, Confezioni]` | Unità di misura disponibili |
| `IMPORTANCE_LEVELS` | `[imp_1, imp_2, imp_3]` | Livelli di importanza del materiale |
| `IMPORTANCE_WEIGHTS` | `[0.50, 0.25, 0.25]` | Probabilità di estrazione per ciascun livello di importanza |
| `COST_MIN` / `COST_MAX` | `23.0` / `42.0` | Range del costo unitario di produzione (€) |
| `MARKUP_MIN` / `MARKUP_MAX` | `3.0` / `4.0` | Range del moltiplicatore applicato al costo per calcolare il prezzo di vendita (`UnitPrice = UnitCost × markup`) |

## `generate_master_customer.py` — anagrafica clienti

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `NUM_CUSTOMERS` | `10` | Numero di clienti da generare |
| `CUSTOMER_TYPES` | `[Ospedale, Farmacia, Grossista, ASL]` | Tipologie di cliente disponibili |
| `COUNTRY_ISO2_CODE` | `"IT"` | Codice paese ISO 3166-1 alpha-2 usato per ricavare le regioni amministrative via `pycountry` |
| `PAYMENT_TERMS` | `[30, 60, 90, 120]` | Dilazioni di pagamento disponibili (giorni) |

## `generate_orders.py` — ordini giornalieri

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `MRK_MIN` / `MRK_MAX` | `3.0` / `4.0` | Range del markup casuale applicato al costo per calcolare `OrderValue` |
| `GRW_MIN` / `GRW_MAX` | `0` / `0.10` | Range del tasso di crescita annua assegnato casualmente a ogni materiale |
| `IMP_CONFIG` | vedi tabella sotto | Configurazione della domanda giornaliera per livello di importanza |

`IMP_CONFIG` per livello — ogni chiave controlla:

| Chiave | Descrizione |
|--------|-------------|
| `qty_min` / `qty_max` | Quantità giornaliera base campionata per ogni riga d'ordine |
| `daily_prob` | Probabilità che il materiale venga ordinato in un dato giorno |
| `cust_max` | Numero massimo di clienti che possono ordinare lo stesso materiale nello stesso giorno |

## `generate_sales.py` — venduto

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `FULFILLMENT_RATE` | `0.85` | Probabilità che un ordine generi almeno una vendita (tasso di evasione) |
| `PARTIAL_RATE` | `0.20` | Tra gli ordini evasi, probabilità che la consegna sia parziale |
| `MIN_PARTIAL_RATIO` | `0.30` | Percentuale minima consegnata nelle consegne parziali (es. `0.30` = almeno 30 % dell'ordinato) |
| `SHIP_EARLY_MAX` | `5` | Massimo anticipo rispetto alla `RequestedDate` (giorni) |
| `SHIP_LATE_MAX` | `10` | Massimo ritardo rispetto alla `RequestedDate` (giorni) |

## `generate_budget.py` — budget mensile

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `BUDGET_GRW_MIN` / `BUDGET_GRW_MAX` | `0.02` / `0.08` | Range del tasso di crescita annua applicato alla proiezione del budget per materiale |
| `BUFFER_MIN` / `BUFFER_MAX` | `-0.15` / `+0.15` | Buffer casuale mensile applicato alla quantità/valore proiettato (±15 %) |

## `generate_inventory.py` — inventario giornaliero

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `AVG_DAILY_FALLBACK` | `1` | Consumo giornaliero minimo usato come fallback se un materiale non ha vendite |
| `INV_CONFIG` | vedi tabella sotto | Configurazione dello stock per livello di importanza |

`INV_CONFIG` per livello:

| Chiave | Descrizione |
|--------|-------------|
| `initial_days` | Stock iniziale espresso in giorni di consumo medio |
| `reorder_point_days` | Soglia di riordino: scatta un rifornimento quando lo stock scende sotto questa soglia (in giorni di consumo medio) |
| `reorder_qty_days` | Quantità riordinata, espressa in giorni di consumo medio |

> **Lead time:** non è definito in `INV_CONFIG`. Viene letto per-item da `MasterMaterial.LeadTimeDays` (**giorni lavorativi**), campionato una volta sola per ogni materiale tramite `LEAD_TIME_CONFIG` in `generate_master_material.py`. Questo garantisce che le analisi di safety stock usino esattamente lo stesso valore utilizzato durante la simulazione.

Il lead time per livello di importanza (range di campionamento):

| Livello | min (gg lavorativi) | max (gg lavorativi) |
|---------|---------------------|---------------------|
| imp_1   | 5                   | 15                  |
| imp_2   | 7                   | 21                  |
| imp_3   | 10                  | 30                  |

## `generate_support_value.py` — valori di supporto

| Parametro | Fonte | Descrizione |
|-----------|-------|-------------|
| `SEASONAL_FACTORS` | `config/seasonal_pattern.json` | Dizionario `mese → [fattore]` caricato a import-time; usato da `generate_orders.py` e `generate_budget.py` per modulare i volumi mensili |
