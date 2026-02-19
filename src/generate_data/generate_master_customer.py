import random
import pycountry
import pandas as pd

from src.utils.utils import on_going_messages
from src.config import  OUTPUT_DIR

#===============================
# master customers configuration
#===============================
# Number of customers to create
NUM_CUSTOMERS = 40

# Customers Type
CUSTOMER_TYPES = ["Ospedale", "Farmacia", "Grossista", "ASL"]

# Customers Region
COUNTRY_ISO2_CODE = "IT"                                                                        # Select country
def get_regions_from_pycountry(country_iso_code2):
    country_all_administration = pycountry.subdivisions.get(country_code = COUNTRY_ISO2_CODE)   # Get all administration from country
    regions_temp = [sub for sub in country_all_administration if sub.type == "Region"]          # Get all regions from country ()
    return [r.name for r in regions_temp]                                                       # Get all regions from country ()
regions = get_regions_from_pycountry(COUNTRY_ISO2_CODE)

# Payment terms (Cambiare con qualcos'altro)
PAYMENT_TERMS = [30, 60, 90, 120]

def generate_master_customer():
    """
    Genera il file MasterCustomer.csv con l'anagrafica dei clienti.

    Returns:
        DataFrame con i dati dei clienti
    """
    on_going_messages("Generating customers...")

    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        customer_type = random.choice(CUSTOMER_TYPES)

        customer = {
            "CustomerID": f"CUST{i:03d}",
            "CustomerName": f"Cliente_{chr(64+i%26)}{i}",
            "CustomerType": customer_type,
            "Region": random.choice(regions),
            "PaymentTerms": random.choice(PAYMENT_TERMS)
        }
        customers.append(customer)

    df = pd.DataFrame(customers)
    df.to_csv(OUTPUT_DIR / "MasterCustomer.csv", index=False)
    on_going_messages("[OK] Generated MasterCustomers.csv")
    return df