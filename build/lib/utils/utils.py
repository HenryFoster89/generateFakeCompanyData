from datetime import datetime


# STAMPA LA DATA
def now():
    """
    Generate a compact timestamp string in the format 'yymmdd-HHMMSS'.

    Returns
    -------
    str
        Current local datetime formatted as 'yymmdd-HHMMSS'.
    """
    timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")
    return timestamp


def on_going_messages(message):
    """
    Print a timestamped message to track ongoing operations.

    Parameters
    ----------
    message : str
        Text to display alongside the current timestamp.
    """
    timestamp = now()
    print(timestamp, message)