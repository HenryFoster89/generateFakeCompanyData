import random
import pandas as pd

from src.utils.utils import on_going_messages
from src.config import  OUTPUT_DIR

#===============================
# master material configuration
#===============================
# Number of items to create
NUM_MATERIALS = 50

PRODUCT_FAMILY = [
        "Antibiotici", "Analgesici", "Cardiovascolari", "Antiinfiammatori",
        "Antidiabetici", "Antipertensivi", "Antistaminici", "Vitamine"
    ]

UNITS = ["Scatole", "Flaconi", "Blister", "Confezioni"]

# Importance classification (three levels)
IMPORTANCE_LEVELS = ["imp_1", "imp_2", "imp_3"]
IMPORTANCE_WEIGHTS = [0.5, 0.25, 0.25]  # 50% high, 25% medium, 25% low

# Unit Cost
COST_MIN = 23.0
COST_MAX = 42.0

# Mark Up (To calculate Unit Price)
MARKUP_MIN = 3.0
MARKUP_MAX = 4.0

# Lead time per importance level (days from replenishment order to receipt).
# Sampled once per material and stored in MasterMaterial so that analyses
# (e.g. safety stock) can reference the item-level lead time directly.
LEAD_TIME_CONFIG = {
    "imp_1": {"min":  5, "max": 15},
    "imp_2": {"min":  7, "max": 21},
    "imp_3": {"min": 10, "max": 30},
}


def generate_master_material():
    """
    Generate masterMaterial.csv file

    Builds NUM_MATERIALS synthetic pharmaceutical product records and saves them
    to OUTPUT_DIR/MasterMaterial.csv. UnitCost is drawn independently per material;
    UnitPrice is derived by applying one random markup factor (sampled once for the
    entire batch) uniformly to all UnitCost values.

    Fields generated:
        MaterialID    (str)   : Sequential unique identifier (format: MATxxx)
        MaterialName  (str)   : Synthetic label built from a letter suffix and index
        Category      (str)   : Therapeutic family, drawn from PRODUCT_FAMILY
        UnitOfMeasure (str)   : Packaging unit, drawn from UNITS
        UnitCost      (float) : Random production cost in [COST_MIN, COST_MAX]
        UnitPrice     (float) : UnitCost × a single random factor in [MARKUP_MIN, MARKUP_MAX]
        Importance    (str)   : Item importance level (imp_1/imp_2/imp_3); drawn from
                                IMPORTANCE_LEVELS with IMPORTANCE_WEIGHTS (50/25/25 %)
        LeadTimeDays  (int)   : Nominal replenishment lead time in days, sampled once per
                                material from LEAD_TIME_CONFIG[importance]

    Returns:
        DataFrame masterMaterial
    """
    on_going_messages("Generating materials...")

    materials = []
    for i in range(1, NUM_MATERIALS + 1):
        importance = random.choices(IMPORTANCE_LEVELS, weights=IMPORTANCE_WEIGHTS, k=1)[0]
        lt_cfg     = LEAD_TIME_CONFIG[importance]
        material = {
            "MaterialID":   f"MAT{i:03d}",
            "MaterialName": f"Farmaco_{chr(64 + ((i-1)%26 + 1))}{i}",
            "Category":     random.choice(PRODUCT_FAMILY),
            "UnitOfMeasure":random.choice(UNITS),
            "UnitCost":     round(random.uniform(COST_MIN, COST_MAX), 2),
            "Importance":   importance,
            "MarkUp":       round(random.uniform(MARKUP_MIN, MARKUP_MAX), 2),
            "LeadTimeDays": random.randint(lt_cfg["min"], lt_cfg["max"]),
        }
        materials.append(material)

    df = pd.DataFrame(materials)
    df["UnitPrice"] = round(df["UnitCost"] * df["MarkUp"],2)
    df = df.drop("MarkUp", axis = 1)
    df.to_csv(OUTPUT_DIR / "MasterMaterial.csv", index=False)
    on_going_messages("[OK] Generated MasterMaterial.csv")
    return df