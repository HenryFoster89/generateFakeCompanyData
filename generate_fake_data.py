#==============================================
# CREATE OUTPUT DIRECTORY
#==============================================
from src.config import OUTPUT_DIR
OUTPUT_DIR.mkdir(exist_ok=True)

#==============================================
# CREATE MASTER MATERIAL CSV
#==============================================
from src.generate_data.generate_master_material import generate_master_material
dfMaMa = generate_master_material()

#=============================================
# CREATE MASTER CUSTOMER CSV
#==============================================
from src.generate_data.generate_master_customer import generate_master_customer
dfMaCu = generate_master_customer()

#==============================================
# CREATE ORDERS
#==============================================
from src.generate_data.generate_orders import generate_ordinato
dfOrd = generate_ordinato(dfMaMa, dfMaCu)