# Goal

Create synthetic data of a pharmaceutical company.

# Output
After running `generate_fake_data.py`, the following `.csv` files will be available in the `data_output` folder:
- MasterMaterial.csv
- MasterCustomer.csv
- Ordinato.csv
- Venduto.csv

## Output description
`MasterMaterial.csv`
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| MaterialID | String | Unique identifier for the material (format: MATxxx) |
| MaterialName | String | Name of the material/drug |
| Category | String | Therapeutic family (e.g., Antibiotici, Analgesici, Cardiovascolari, etc.) |
| UnitOfMeasure | String | Packaging unit (e.g., Scatole, Flaconi, Confezioni, Blister) |
| UnitCost | Float | Production cost per unit |
| UnitPrice | Float | Selling price per unit (UnitCost × a single random markup factor) |
| Importance | String | Item importance level: imp_1 (~50%), imp_2 (~25%), imp_3 (~25%) |

`MasterCustomer.csv`
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| CustomerID | String | Unique identifier for the customer (format: CUSTxxx) |
| CustomerName | String | Synthetic customer label |
| CustomerType | String | Type of customer (Ospedale, Farmacia, Grossista, ASL) |
| Region | String | Italian administrative region |
| PaymentTerms | Integer | Payment delay in days (30, 60, 90, or 120) |

`Ordinato.csv`
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| OrderID | String | Unique identifier for the order (format: ORDxxxxxx) |
| OrderDate | String | Order creation date (YYYY-MM-DD) |
| RequestedDate | String | Requested delivery date (7–60 days after OrderDate) |
| MaterialID | String | Reference to MasterMaterial |
| CustomerID | String | Reference to MasterCustomer |
| QuantityOrdered | Integer | Units ordered by this customer on this day |
| OrderValue | Float | Revenue (QuantityOrdered × UnitCost × random markup) |

`Venduto.csv`
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| SaleID | String | Unique identifier for the sale (format: SALExxxxxx) |
| OrderID | String | Reference to the originating order in Ordinato.csv |
| OrderDate | String | Order creation date (copied from the order) |
| ShipmentDate | String | Actual shipment date (RequestedDate ± a few days) |
| MaterialID | String | Reference to MasterMaterial |
| CustomerID | String | Reference to MasterCustomer |
| QuantityOrdered | Integer | Original quantity from the order (reference) |
| QuantitySold | Integer | Actual quantity delivered (≤ QuantityOrdered) |
| SaleValue | Float | Revenue (OrderValue scaled by QuantitySold / QuantityOrdered) |

The seasonal pattern used to modulate order volumes can be customized by modifying the file in the `config` folder:
- `seasonal_pattern.json`
