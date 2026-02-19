import random
import pandas as pd

from src.utils.utils import on_going_messages
from src.config import  OUTPUT_DIR

#===============================
# master material configuration
#===============================
# Number of items to create
NUM_MATERIALS = 25

PRODUCT_FAMILY = [
        "Antibiotici", "Analgesici", "Cardiovascolari", "Antiinfiammatori",
        "Antidiabetici", "Antipertensivi", "Antistaminici", "Vitamine"
    ]

UNITS = ["Scatole", "Flaconi", "Blister", "Confezioni"]

# Unit Cost
COST_MIN = 23.0
COST_MAX = 42.0

# Mark Up (To calculate Unit Price)
MARKUP_MIN = 3.0
MARKUP_MAX = 4.0


def generate_master_material():
    """
    Generate masterMaterial.csv file

    Returns:
        DataFrame masterMaterial
    """
    on_going_messages("Generating materials...")

    materials = []
    for i in range(1, NUM_MATERIALS + 1):
        material = {
            "MaterialID": f"MAT{i:03d}",
            "MaterialName": f"Farmaco_{chr(64+i%26)}{i}",
            "Category": random.choice(PRODUCT_FAMILY),
            "UnitOfMeasure": random.choice(UNITS),
            "UnitCost": round(random.uniform(COST_MIN, COST_MAX), 2),
            #"TargetInventoryDays": random.choice([30, 45, 60, 90])
        }
        materials.append(material)

    df = pd.DataFrame(materials)
    df["UnitPrice"] = round(df["UnitCost"] * random.uniform(MARKUP_MIN, MARKUP_MAX),2)
    df.to_csv(OUTPUT_DIR / "MasterMaterial.csv", index=False)
    on_going_messages("[OK] Generated MasterMaterial.csv")
    return df