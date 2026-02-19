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
    """
    Returns a list of region names for the given ISO 3166-1 alpha-2 country code.

    Queries pycountry for all administrative subdivisions of the country and
    filters only those whose type is 'Region' (level-1 administrative divisions).

    Args:
        country_iso_code2 (str): Two-letter ISO country code (e.g. 'IT' for Italy)

    Returns:
        List[str]: Names of administrative subdivisions of type 'Region'
    """
    country_all_administration = pycountry.subdivisions.get(country_code = COUNTRY_ISO2_CODE)   # Get all administration from country
    regions_temp = [sub for sub in country_all_administration if sub.type == "Region"]          # Get all regions from country ()
    return [r.name for r in regions_temp]                                                       # Get all regions from country ()
regions = get_regions_from_pycountry(COUNTRY_ISO2_CODE)

# Payment terms (Cambiare con qualcos'altro)
PAYMENT_TERMS = [30, 60, 90, 120]

def generate_master_customer():
    """
    Genera il file MasterCustomer.csv con l'anagrafica dei clienti.

    Builds NUM_CUSTOMERS synthetic customer records and saves them to
    OUTPUT_DIR/MasterCustomer.csv. Each customer is assigned a random type,
    an Italian administrative region, and a payment term drawn from PAYMENT_TERMS.

    Fields generated:
        CustomerID   (str) : Sequential unique identifier (format: CUSTxxx)
        CustomerName (str) : Synthetic label built from a letter suffix and index
        CustomerType (str) : One of CUSTOMER_TYPES (e.g. Ospedale, Farmacia)
        Region       (str) : Random Italian administrative region
        PaymentTerms (int) : Payment delay in days, drawn from PAYMENT_TERMS

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