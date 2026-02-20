import json

from src.config import SEASONAL_PATTERN_PATH

# Seasonal factors by month (1-12), loaded once at import time
with open(SEASONAL_PATTERN_PATH, "r") as _f:
    SEASONAL_FACTORS = json.load(_f)
