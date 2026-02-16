# Goal

Create synthetic data of a pharmaceutical company.

# Output
After running `generate_fake_data.py`, the following `.csv` files will be available in the `data_output` folder:
- MasterMaterial.csv
- MasterCustomer.csv

TODO (in maniera ordinata rispetto l'iterazione)
- Budget.csv
- Forecast.csv
- LivelloInventario.csv
- Ordinato.csv
- Venduto.csv

## Output description
`MasterMaterial.csv` 
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| MaterialID | String | Unique identifier for the material |
| MaterialName | String | Name of the material/drug |
| Category | String | Category of the drug (e.g., Analgesici, Antiinfiammatori, etc.) |
| UnitOfMeasure | String | Unit of measure (e.g., Scatole, Flaconi, Confezioni, Blister) |
| UnitCost | Float | Cost per unit |
| TargetInventoryDays | Integer | Target number of days to keep in inventory |


`categories` and `units` can be customized by modifying the files in the `config` folder:
- `masterMaterial_categories.json`
- `masterMaterial_units.json`
