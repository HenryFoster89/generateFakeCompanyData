import sys
import os
from pathlib import Path

# Cambia la working directory alla root del progetto
root_dir = Path(__file__).parent.parent
os.chdir(root_dir)
sys.path.insert(0, str(root_dir))

print(f"Working directory cambiata a: {os.getcwd()}")

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

#==============================================
# CREATE MASTER CUSTOMER CSV
#==============================================
from src.generate_data.generate_master_customer import generate_master_customer
dfMaCu = generate_master_customer()

#==============================================
# CREATE ORDERS
#==============================================
from src.generate_data.generate_orders import generate_ordinato
dfOrd = generate_ordinato(dfMaMa, dfMaCu)