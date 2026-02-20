from pathlib import Path
from datetime import datetime
# Configurazione globale
OUTPUT_DIR            = Path("data_output")
SEASONAL_PATTERN_PATH = Path("config") / "seasonal_pattern.json"
DB_PATH               = OUTPUT_DIR / "company_data.db"

# Time window (shared by orders, sales, budget)
START_DATE      = datetime(2023, 1, 1)
MONTHS_HISTORY  = 36
MONTHS_FORECAST = 12



#====================
# CANCELLARE
#====================

# Creare cartella output se non esiste
#OUTPUT_DIR.mkdir(exist_ok=True)



