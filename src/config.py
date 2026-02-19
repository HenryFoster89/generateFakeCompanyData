import random
import numpy as np
from pathlib import Path
from datetime import datetime

# Configurazione seed per riproducibilità
np.random.seed(42)
random.seed(42)

# Configurazione globale
OUTPUT_DIR = Path("data_output")


MONTHS_FORECAST = 12



#====================
# CANCELLARE
#====================

# Creare cartella output se non esiste
#OUTPUT_DIR.mkdir(exist_ok=True)



