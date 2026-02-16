import random
import pandas as pd

from src.utils.utils import on_going_messages
from src.config import NUM_MATERIALS, OUTPUT_DIR

def generate_master_material():
    """
    Generate masterMaterial.csv file

    Returns:
        DataFrame masterMaterial
    """
    on_going_messages("Generating materials...")

    # Categorie farmaceutiche comuni
    categories = [
        "Antibiotici", "Analgesici", "Cardiovascolari", "Antiinfiammatori",
        "Antidiabetici", "Antipertensivi", "Antistaminici", "Vitamine"
    ]

    # Unità di misura
    units = ["Scatole", "Flaconi", "Blister", "Confezioni"]

    materials = []
    for i in range(1, NUM_MATERIALS + 1):
        material = {
            "MaterialID": f"MAT{i:03d}",
            "MaterialName": f"Farmaco_{chr(64+i%26)}{i}",
            "Category": random.choice(categories),
            "UnitOfMeasure": random.choice(units),
            "UnitCost": round(random.uniform(5, 150), 2),
            "TargetInventoryDays": random.choice([30, 45, 60, 90])
        }
        materials.append(material)

    df = pd.DataFrame(materials)
    df.to_csv(OUTPUT_DIR / "MasterMaterial.csv", index=False)
    on_going_messages("[OK] Generated MasterMaterial.csv")
    return df