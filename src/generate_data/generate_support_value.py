import json
from datetime import datetime

def generate_date_range(start_date, months):
    """
    Generate a list of monthly dates.

    Args:
        start_date: Starting date
        months: Number of months to generate

    Returns:
        List of Dates (first day of each month)
    """
    
    dates = []
    current = start_date
    for _ in range(months):
        dates.append(current)
        # Passare al primo giorno del mese successivo
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    return dates


def generate_seasonal_factor(month):
    """
    Genera un fattore stagionale per simulare variazioni nelle vendite farmaceutiche.

    Args:
        month: Mese (1-12)

    Returns:
        Fattore moltiplicativo (0.7 - 1.3)
    """

    try:
        #TODO move pathname to config.py
        with open(r'config\seasonal_pattern.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("Error: File not found.")
    
    #TODO  Check with old version
    return data[month][0]