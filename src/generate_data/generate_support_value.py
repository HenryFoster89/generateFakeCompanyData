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
