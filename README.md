# Goal

Create synthetic data of a pharmaceutical company for analytics and BI use cases.

---

## Indice

- [Project structure](#project-structure)
- [Output](#output)
- [Output description](#output-description)
  - [MasterMaterial.csv](#mastermaterialcsv)
  - [MasterCustomer.csv](#mastercustomercsv)
  - [Ordinato.csv](#ordinatocsv)
  - [Venduto.csv](#vendutocsv)
  - [Budget.csv](#budgetcsv)
  - [Inventario.csv](#inventariocsv)
  - [Forecast.csv](#forecastcsv)
- [SQLite Database](#sqlite-database)
- [Configuration](#configuration)
- [Parametri](#parametri)
  - [src/config.py](#srcconfigpy--parametri-globali)
  - [generate\_master\_material.py](#generate_master_materialpy--anagrafica-materiali)
  - [generate\_master\_customer.py](#generate_master_customerpy--anagrafica-clienti)
  - [generate\_orders.py](#generate_orderspy--ordini-giornalieri)
  - [generate\_sales.py](#generate_salespy--venduto)
  - [generate\_budget.py](#generate_budgetpy--budget-mensile)
  - [generate\_inventory.py](#generate_inventorypy--inventario-giornaliero)
  - [generate\_forecast.py](#generate_forecastpy--forecast-mensile-domanda)
  - [generate\_support\_value.py](#generate_support_valuepy--valori-di-supporto)
- [Analisi](#analisi)
  - [Supply Chain & Inventario](#supply-chain--inventario)
  - [Vendite & Budget](#vendite--budget)
  - [Ordini & OTIF](#ordini--otif)
  - [Clienti & Margini](#clienti--margini)
  - [Forecast Accuracy](#forecast-accuracy)
- [Architettura analitica — decisione aperta](#architettura-analitica--decisione-aperta)
- [Tabelle da aggiungere](#tabelle-da-aggiungere)

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
│   ├── generate_forecast.py         # Forecast mensile domanda (H=1…15)
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
├── Forecast.csv
└── company_data.db                  # SQLite DB (ricreato ad ogni run)
```

---

# Output

After running the pipeline, the following files are available in `data_output/`:

| File | Descrizione |
|------|-------------|
| `MasterMaterial.csv` | Anagrafica materiali |
| `MasterCustomer.csv` | Anagrafica clienti |
| `Ordinato.csv` | Ordini giornalieri (24 mesi) |
| `Venduto.csv` | Vendite consuntivate |
| `Budget.csv` | Budget mensile per materiale (storico + forecast 12 mesi) |
| `Inventario.csv` | Inventario giornaliero per materiale (modello reorder point) |
| `Forecast.csv` | Forecast mensile domanda per materiale — 15 orizzonti (H=1…15) |
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

Granularità **mensile**. Copre l'intero storico (24 mesi) più 12 mesi di forecast. Calcolato aggregando lo storico degli ordini per materiale e proiettandolo con crescita annua e stagionalità.

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

## Forecast.csv

Granularità **mensile per materiale per orizzonte previsionale**. Genera previsioni di domanda a 15 orizzonti (H=1 … H=15 mesi) per l'intera finestra temporale (storico + forecast).

Il modello simula un forecaster reale:
- ogni materiale ha un **bias stabile** (errore sistematico: sovra- o sotto-stima costante nel tempo)
- il **rumore cresce linearmente con l'orizzonte**: ±10 % a H=1, fino a ±45 % a H=15

Per i mesi storici (MONTHS_HISTORY) la base è la quantità effettiva venduta; per i mesi futuri si usa la media storica corretta per stagionalità e crescita.

L'analisi di **forecast accuracy** (MAPE, MAE, Bias) si calcola unendo questa tabella con `Venduto` su `(MaterialID, ForecastMonth = YearMonth)`, filtrando sui mesi storici dove esiste l'actual.

| Column | Type | Description |
|--------|------|-------------|
| ForecastID | String | Identificatore univoco (formato: FCSTxxxxxxx) |
| ForecastMadeOn | String | Mese in cui il forecast è stato prodotto (YYYY-MM) = `ForecastMonth − Horizon` |
| ForecastMonth | String | Mese previsto (YYYY-MM) |
| MaterialID | String | Riferimento a MasterMaterial |
| Horizon | Integer | Orizzonte previsionale in mesi (1 … 15) |
| ForecastQty | Integer | Quantità prevista (min 1) |
| ForecastValue | Float | Valore previsto (ForecastQty × UnitPrice) |

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
| `MONTHS_HISTORY` | `24` | Mesi di storico da generare |
| `MONTHS_FORECAST` | `12` | Mesi di forecast aggiuntivi (usato da Budget e Forecast) |
| `OUTPUT_DIR` | `data_output/` | Cartella di output per tutti i CSV e il DB |
| `SEASONAL_PATTERN_PATH` | `config/seasonal_pattern.json` | Percorso del file JSON con i fattori stagionali mensili |
| `DB_PATH` | `data_output/company_data.db` | Percorso del database SQLite |

## `generate_master_material.py` — anagrafica materiali

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `NUM_MATERIALS` | `374` | Numero di materiali (SKU) da generare |
| `PRODUCT_FAMILY` | lista 8 elementi | Famiglie terapeutiche assegnabili a ciascun materiale |
| `UNITS` | `[Scatole, Flaconi, Blister, Confezioni]` | Unità di misura disponibili |
| `IMPORTANCE_LEVELS` | `[imp_1, imp_2, imp_3]` | Livelli di importanza del materiale |
| `IMPORTANCE_WEIGHTS` | `[0.50, 0.25, 0.25]` | Probabilità di estrazione per ciascun livello di importanza |
| `COST_MIN` / `COST_MAX` | `23.0` / `42.0` | Range del costo unitario di produzione (€) |
| `MARKUP_MIN` / `MARKUP_MAX` | `3.0` / `4.0` | Range del moltiplicatore applicato al costo per calcolare il prezzo di vendita (`UnitPrice = UnitCost × markup`) |

## `generate_master_customer.py` — anagrafica clienti

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `NUM_CUSTOMERS` | `1453` | Numero di clienti da generare |
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

## `generate_forecast.py` — forecast mensile domanda

| Parametro | Valore default | Descrizione |
|-----------|----------------|-------------|
| `HORIZONS` | `[1 … 15]` | Orizzonti previsionali generati (mesi avanti) |
| `NOISE_BASE` | `0.10` | Ampiezza del rumore (±%) all'orizzonte H=1 |
| `NOISE_SLOPE` | `0.025` | Incremento del rumore per ogni mese aggiuntivo di orizzonte (+2.5 pp/mese) |
| `BIAS_MIN` / `BIAS_MAX` | `-0.10` / `+0.15` | Range del bias casuale stabile per materiale (errore sistematico: sotto- o sovra-stima) |
| `FORECAST_GRW_MIN` / `FORECAST_GRW_MAX` | `0.02` / `0.08` | Range del tasso di crescita annua usato per estrapolare i mesi futuri (dove non esistono vendite reali) |

Il rumore per orizzonte si calcola come: `noise_amp = NOISE_BASE + NOISE_SLOPE × (H − 1)`, che produce i seguenti MAPE attesi:

| Orizzonte | Rumore (±%) | MAPE atteso |
|-----------|-------------|-------------|
| H=1       | ±10 %       | ~8–12 %     |
| H=3       | ±15 %       | ~12–18 %    |
| H=6       | ±22.5 %     | ~18–26 %    |
| H=12      | ±37.5 %     | ~30–40 %    |
| H=15      | ±45 %       | ~36–48 %    |

## `generate_support_value.py` — valori di supporto

| Parametro | Fonte | Descrizione |
|-----------|-------|-------------|
| `SEASONAL_FACTORS` | `config/seasonal_pattern.json` | Dizionario `mese → [fattore]` caricato a import-time; usato da `generate_orders.py`, `generate_budget.py` e `generate_forecast.py` per modulare i volumi mensili |

---

# Analisi

Tipologie di analisi realizzabili con i dati generati. Tutte le analisi sono basate sulle tabelle disponibili in `data_output/company_data.db`.

## Supply Chain & Inventario

| Analisi | Tabelle coinvolte | Done |
|---------|-------------------|------|
| Evoluzione stock giornaliero per materiale (sawtooth) | Inventario | No |
| Giorni di stockout per materiale / periodo | Inventario | No |
| Fill Rate (ClosingStock > 0 / totale giorni) | Inventario | No |
| Safety Stock effettivo vs teorico (σ domanda × √LeadTime) | Inventario, MasterMaterial, Venduto | No |
| Giorni di copertura residui per materiale | Inventario, Venduto | No |
| Analisi ABC per valore di stock (OpeningStock × UnitCost) | Inventario, MasterMaterial | No |
| Frequenza e dimensione dei rifornimenti (DailyInflow > 0) | Inventario | No |
| Confronto LeadTimeDays teorico vs gap reale tra ordine e consegna | MasterMaterial, Ordinato, Venduto | No |

## Vendite & Budget

| Analisi | Tabelle coinvolte | Done |
|---------|-------------------|------|
| Actual vs Budget (Qty e Value) per materiale / mese | Venduto, Budget | No |
| Scostamento % Budget per categoria terapeutica | Venduto, Budget, MasterMaterial | No |
| Trend di crescita annua per materiale (CAGR) | Venduto | No |
| Stagionalità delle vendite (volume mensile normalizzato) | Venduto | No |
| Revenue breakdown per categoria terapeutica | Venduto, MasterMaterial | No |
| Analisi ABC per fatturato (Pareto 80/20) | Venduto, MasterMaterial | No |
| Analisi XYZ per variabilità domanda (CV = σ/μ mensile) | Venduto | No |
| Matrice ABC-XYZ per prioritizzazione SKU | Venduto, MasterMaterial | No |

## Ordini & OTIF

| Analisi | Tabelle coinvolte | Done |
|---------|-------------------|------|
| OTIF — On Time In Full (ordini evasi completi entro RequestedDate) | Ordinato, Venduto | No |
| Tasso di evasione ordini (Fulfillment Rate) | Ordinato, Venduto | No |
| Tasso di consegne parziali (Partial Rate) | Venduto | No |
| Ritardo medio di spedizione (ShipmentDate − RequestedDate) | Ordinato, Venduto | No |
| Volume ordinato vs spedito per materiale / periodo | Ordinato, Venduto | No |
| Ordini inevasi (OrderID in Ordinato non presenti in Venduto) | Ordinato, Venduto | No |

## Clienti & Margini

| Analisi | Tabelle coinvolte | Done |
|---------|-------------------|------|
| Fatturato per cliente (ranking) | Venduto, MasterCustomer | No |
| Fatturato per tipo cliente (Ospedale, Farmacia, Grossista, ASL) | Venduto, MasterCustomer | No |
| Fatturato per regione geografica | Venduto, MasterCustomer | No |
| Margine lordo per materiale (SaleValue − QuantitySold × UnitCost) | Venduto, MasterMaterial | No |
| Margine lordo per categoria terapeutica | Venduto, MasterMaterial | No |
| Analisi DSO (Days Sales Outstanding) per cliente | Venduto, MasterCustomer | No |
| Mix clienti per materiale (quali clienti ordinano quali SKU) | Ordinato, MasterCustomer | No |

## Forecast Accuracy

Confronto tra domanda prevista (Forecast) e domanda reale (Venduto aggregato per mese), filtrando i mesi storici dove esistono entrambi i valori.

| Analisi | Tabelle coinvolte | Done |
|---------|-------------------|------|
| MAPE (Mean Absolute Percentage Error) per materiale e orizzonte | Forecast, Venduto | No |
| MAE (Mean Absolute Error) per materiale e orizzonte | Forecast, Venduto | No |
| Bias (errore sistematico medio: sovra- vs sotto-stima) per materiale | Forecast, Venduto | No |
| Accuracy vs Orizzonte — curva MAPE medio per H=1…15 | Forecast, Venduto | No |
| Distribuzione errori di forecast (istogramma per orizzonte) | Forecast, Venduto | No |
| Materiali con peggior/miglior accuracy (ranking per MAPE a H=3) | Forecast, Venduto, MasterMaterial | No |

---

# Architettura analitica — decisione aperta

## Contesto

Il deliverable finale è un sito **GitHub Pages** (statico: HTML + CSS + JS) da affiancare al CV.
Il DB SQLite è generato in questo progetto e spostato nel progetto portfolio.

## Vincolo tecnico

GitHub Pages **non può eseguire Python né interrogare SQLite a runtime**. Serve solo file statici.
Conseguenza: il DB è uno strumento intermedio, non la fonte dati live del portfolio.

## Opzioni discusse

### Opzione A — SQL views + JS diretto sul DB

- Creare viste SQL nel DB per incapsulare la logica di business (OTIF, fulfillment rate, margini, ecc.)
- Il sito JS interroga il DB tramite **sql.js** (SQLite compilato in WebAssembly)
- **Pro**: logica di business centralizzata nel DB; queryabile da qualsiasi tool esterno
- **Contro**: sql.js è pesante; alcune analisi (ABC-XYZ, safety stock, CAGR) richiedono `STDDEV` e `PERCENTILE_CONT` che SQLite non supporta nativamente

### Opzione B — Python scripts → JSON → JS (consigliata)

- Script Python (`analytics/`) leggono dal DB, calcolano i KPI, esportano JSON pre-aggregati
- Il sito GitHub Pages legge i JSON e li plotta con **Chart.js** o **Plotly.js**
- **Pro**: piena potenza statistica in Python; JSON leggeri; nessun vincolo SQL; output versionabile
- **Contro**: logica analitica dispersa tra Python e JS; il DB non è più "interrogabile" dal portfolio

### Opzione C — Python → HTML statici (Plotly export)

- Python genera file HTML auto-contenuti (`plotly fig.write_html()`) per ogni grafico
- GitHub Pages li serve direttamente, senza bisogno di JS aggiuntivo
- **Pro**: zero JS sul portfolio; grafici interattivi già pronti
- **Contro**: file HTML pesanti; meno flessibilità nel layout del sito

### Opzione D — DB only qui, tutta la logica analitica nel portfolio

- Questo progetto produce **solo** il DB SQLite (nessuno script di analisi)
- Il progetto `portfolioGitHub` contiene tutta la logica: KPI, grafici, layout
- Il portfolio è quindi **autosufficiente e completo** — chi lo vede insieme al CV trova tutto in un posto
- **Pro**: separazione netta dei ruoli (questo progetto = generazione dati; portfolio = analisi + presentazione); il portfolio dimostra sia le competenze analitiche che quelle di visualizzazione
- **Contro**: questo progetto diventa un generatore di dati "muto", senza strato analitico autonomo

### Opzione E — Questo progetto diventa un sotto-pacchetto di portfolioGitHub

- `generateFakeCompanyData` viene inglobato in `portfolioGitHub` come modulo interno (o sottorepository)
- L'unico progetto pubblico è `portfolioGitHub`, che fa tutto in sequenza:
  1. Genera il DB (logica di questo progetto)
  2. Calcola i KPI (Python)
  3. Produce i JSON pre-aggregati
  4. Serve HTML + CSS + JS per la visualizzazione
- **Pro**: repository unico, pipeline end-to-end visibile tutta in un posto; chi visita il portfolio vede l'intera catena; nessuna dipendenza esterna da gestire
- **Contro**: il progetto portfolio diventa più grande e meno focalizzato sulla presentazione; la logica di generazione dati e quella di visualizzazione sono mescolate nello stesso repository

## Domande aperte prima di decidere

1. Il portfolio avrà un layout personalizzato (HTML/CSS custom) o userà un template/framework?
2. È necessario che il DB sia interrogabile interattivamente dall'utente del sito, o bastano grafici fissi?
3. Quanto JS si vuole scrivere nel progetto portfolio?
4. Si vuole che questo progetto abbia valore standalone (con analisi proprie), o serve solo come generatore per il portfolio?
5. Si preferisce avere **due repository separati** (generazione dati / portfolio) o **un unico repository** che fa tutto?

---

## Considerazioni e raccomandazione

### Opzioni da escludere subito

- **Opzione A** (sql.js): eccessivamente complessa, sql.js pesa ~1 MB, e le analisi statistiche più importanti (ABC-XYZ, safety stock, CAGR) non sono implementabili in SQLite standard. Non vale lo sforzo.
- **Opzione C** (HTML Plotly export): i file HTML auto-contenuti di Plotly pesano 3–5 MB ciascuno. Con 29 analisi, il portfolio sarebbe impraticabile su mobile e lento anche su desktop. Da evitare.
- **Opzione E** (repo unico): mescolare generazione dati, analytics e frontend in un unico repository rende tutto più difficile da leggere, testare e mantenere. Riduce anche la leggibilità del portfolio stesso, che dovrebbe essere focalizzato sulla presentazione.

### Raccomandazione: Opzione B — con analytics in questo progetto

La scelta migliore è tenere **due repository con responsabilità separate**:

```
[generateFakeCompanyData]           [portfolioGitHub]
  ├── genera il DB                    ├── legge i JSON
  ├── calcola tutti i KPI             ├── plotta con Chart.js o Plotly.js
  └── esporta JSON pre-aggregati      └── HTML + CSS + layout
          ↓
     data_output/analytics/
     ├── kpi_otif.json
     ├── kpi_abc_xyz.json
     ├── kpi_revenue_by_category.json
     └── ...
```

**Perché questa scelta:**

1. **Questo progetto resta autonomo e dimostrativo** — chi arriva su questo repository vede non solo la generazione dati ma anche la logica analitica completa in Python. È un progetto di data engineering + analytics a sé stante.

2. **Il portfolio fa solo il frontend** — responsabilità unica, codice pulito, facile da mantenere. Non deve sapere nulla di SQL, pandas o scipy.

3. **I JSON sono il contratto tra i due progetti** — file leggeri, versionabili, leggibili. Se un'analisi cambia, si rigenera il JSON e il portfolio si aggiorna automaticamente.

4. **Nessun vincolo SQL** — Python ha piena potenza statistica (numpy, scipy, pandas) per calcolare tutto: ABC-XYZ, CAGR, safety stock teorico, DSO, CV.

5. **Opzione C rimane un fallback** — se non si vuole scrivere JS nel portfolio, si può usare Plotly per esportare HTML leggeri (non auto-contenuti) che referenziano la CDN. Il layout rimarrebbe meno flessibile ma richiederebbe zero JS.

### Struttura JSON suggerita per ogni analisi

Ogni file JSON contiene due chiavi: `meta` (descrizione dell'analisi, tabelle usate, data di generazione) e `data` (array di record pronti per essere plottati). Questo rende i file auto-documentanti e facilmente consumabili da qualsiasi libreria JS.

---

# Tabelle da aggiungere

Tabelle non ancora implementate, identificate durante la progettazione del modello dati.

## Proposta utente

### `Forecast` — forecast mensile domanda *(implementata)*

Tabella già implementata in questa sessione. Vedi sezione [Forecast.csv](#forecastcsv) per il dettaglio.

## Proposte assistente

### `Pagamenti` — registrazione pagamenti effettivi *(critica)*

**Motivazione:** `MasterCustomer.PaymentTerms` indica la dilazione contrattuale (30/60/90/120 giorni), ma non il pagamento effettivo. Senza questa tabella, l'analisi DSO (Days Sales Outstanding) non è calcolabile realisticamente — si può solo stimare usando la data di spedizione + PaymentTerms, senza varianza.

**Schema proposto:**

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| PaymentID | String | Identificatore univoco |
| SaleID | String | Riferimento a Venduto |
| CustomerID | String | Riferimento a MasterCustomer |
| InvoiceDate | String | Data di emissione fattura (tipicamente = ShipmentDate) |
| DueDate | String | Data di scadenza (InvoiceDate + PaymentTerms) |
| ActualPaymentDate | String | Data di pagamento effettivo (DueDate ± varianza casuale) |
| AmountPaid | Float | Importo pagato |

**Analisi abilitate:** DSO reale per cliente, aging del credito, tasso di ritardo pagamenti, distribuzione giorni di ritardo.

---

### `Resi` — resi merce *(opzionale)*

**Motivazione:** simulare un tasso di reso del ~5 % delle righe venduta permette di calcolare il fatturato netto reale e il tasso di reso per materiale/categoria/cliente.

**Schema proposto:**

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| ReturnID | String | Identificatore univoco |
| SaleID | String | Riferimento a Venduto |
| MaterialID | String | Riferimento a MasterMaterial |
| CustomerID | String | Riferimento a MasterCustomer |
| ReturnDate | String | Data del reso (YYYY-MM-DD) |
| QuantityReturned | Integer | Unità restituite |
| ReturnValue | Float | Valore reso (QuantityReturned × UnitPrice) |

**Analisi abilitate:** tasso di reso per materiale/categoria/cliente, fatturato netto (SaleValue − ReturnValue), impatto resi sul margine.

---

### `DimDate` — dimensione calendario *(utility BI)*

**Motivazione:** tabella di utilità standard nei data warehouse. Evita di ricalcolare anno/trimestre/mese/settimana/IsWorkingDay a ogni query.

**Schema proposto:**

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| Date | String | Data (YYYY-MM-DD) — chiave primaria |
| Year | Integer | Anno |
| Quarter | Integer | Trimestre (1–4) |
| Month | Integer | Mese (1–12) |
| MonthName | String | Nome mese (Gennaio, …) |
| Week | Integer | Numero settimana ISO |
| IsWorkingDay | Integer | 1 se giorno lavorativo, 0 altrimenti |

**Analisi abilitate:** qualsiasi aggregazione per periodo (YTD, QTD, MTD) senza logica di data nelle query.

---
