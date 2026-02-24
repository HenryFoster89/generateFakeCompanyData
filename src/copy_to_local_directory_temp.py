"""
src/copy_to_local_directory_temp.py
------------------------------------
Copia tutti i file JSON generati in data_output/analytics/
verso la cartella locale del portfolio Git Pages.

Destinazione aggiuntiva:
    C:/Users/Enrico.Stancanelli/OneDrive - Dayco/Desktop/ForteChance/portfolioGitPages/data/json

Utilizzo:
    python -m src.copy_to_local_directory_temp
"""

import shutil
from pathlib import Path

from src.utils.utils import on_going_messages

ANALYTICS_DIR   = Path("data_output") / "analytics"
PORTFOLIO_DIR   = Path("C:/Users/Enrico.Stancanelli/OneDrive - Dayco/Desktop/ForteChance/portfolioGitPages/data/json")


def copy_json_to_portfolio() -> None:
    """
    Copia tutti i file .json presenti in ANALYTICS_DIR verso PORTFOLIO_DIR.

    Crea PORTFOLIO_DIR se non esiste.
    Sovrascrive i file esistenti nella destinazione.
    """
    if not ANALYTICS_DIR.exists():
        on_going_messages(f"[SKIP] Cartella sorgente non trovata: {ANALYTICS_DIR}")
        return

    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

    json_files = list(ANALYTICS_DIR.glob("*.json"))

    if not json_files:
        on_going_messages("[SKIP] Nessun file JSON trovato in analytics/")
        return

    for src_file in json_files:
        dst_file = PORTFOLIO_DIR / src_file.name
        shutil.copy2(src_file, dst_file)
        on_going_messages(f"[OK] Copiato: {src_file.name} -> {dst_file}")

    on_going_messages(f"[OK] {len(json_files)} file JSON copiati in {PORTFOLIO_DIR}")


if __name__ == "__main__":
    copy_json_to_portfolio()
