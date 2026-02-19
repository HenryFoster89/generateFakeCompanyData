# Goal

Create synthetic data of a pharmaceutical company for analytics and BI use cases.

---

# Project structure

```
src/
├── config.py                        # Global constants (paths, dates, seeds)
├── generate_data/
│   ├── generate_master_material.py  # Anagrafica materiali
│   ├── generate_master_customer.py  # Anagrafica clienti
│   ├── generate_orders.py           # Ordinato giornaliero
│   ├── generate_sales.py            # Venduto (da ordini)
│   ├── generate_budget.py           # Budget mensile per materiale
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
