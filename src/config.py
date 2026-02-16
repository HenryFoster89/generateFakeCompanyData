import random
import numpy as np
from pathlib import Path
from datetime import datetime

# Configurazione seed per riproducibilità
np.random.seed(42)
random.seed(42)

# Configurazione globale
OUTPUT_DIR = Path("data_output")
NUM_MATERIALS = 18
NUM_CUSTOMERS = 40
MONTHS_HISTORY = 36
MONTHS_FORECAST = 12
START_DATE = datetime(2023, 1, 1)


#====================
# CANCELLARE
#====================

# Creare cartella output se non esiste
#OUTPUT_DIR.mkdir(exist_ok=True)



