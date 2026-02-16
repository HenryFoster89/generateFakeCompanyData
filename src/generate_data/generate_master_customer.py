import random
import pandas as pd

from src.utils.utils import on_going_messages
from src.config import NUM_CUSTOMERS, OUTPUT_DIR

def generate_master_customer():
    """
    Genera il file MasterCustomer.csv con l'anagrafica dei clienti.

    Returns:
        DataFrame con i dati dei clienti
    """
    on_going_messages("Generating customers...")

    customer_types = ["Ospedale", "Farmacia", "Grossista", "ASL"]
    regions = ["Nord", "Centro", "Sud", "Isole"]
    payment_terms = [30, 60, 90, 120]

    # Nomi realistici per i clienti
    hospital_names = ["San Raffaele", "Policlinico", "Ospedale Civile", "Clinica Santa Maria"]
    pharmacy_names = ["Farmacia Centrale", "Farmacia del Corso", "Farmacia Moderna"]
    grossist_names = ["Grossista Pharma", "Distribuzione Farmaci"]
    asl_names = ["ASL"]

    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        customer_type = random.choice(customer_types)

        # Nome cliente basato sul tipo
        if customer_type == "Ospedale":
            base_name = random.choice(hospital_names)
        elif customer_type == "Farmacia":
            base_name = random.choice(pharmacy_names)
        elif customer_type == "Grossista":
            base_name = random.choice(grossist_names)
        else:
            base_name = random.choice(asl_names)

        customer = {
            "CustomerID": f"CUST{i:03d}",
            "CustomerName": f"{base_name} {i}",
            "CustomerType": customer_type,
            "Region": random.choice(regions),
            "PaymentTerms": random.choice(payment_terms)
        }
        customers.append(customer)

    df = pd.DataFrame(customers)
    df.to_csv(OUTPUT_DIR / "MasterCustomer.csv", index=False)
    on_going_messages("[OK] Generated MasterCustomers.csv")
    return df