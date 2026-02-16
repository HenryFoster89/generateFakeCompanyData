import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import random

# Configurazione seed per riproducibilità
np.random.seed(42)
random.seed(42)

# Configurazione globale
OUTPUT_DIR = Path("data_output")
NUM_MATERIALS = 18
NUM_CUSTOMERS = 40
MONTHS_HISTORY = 36
MONTHS_FORECAST = 12

# Creare cartella output se non esiste
OUTPUT_DIR.mkdir(exist_ok=True)
