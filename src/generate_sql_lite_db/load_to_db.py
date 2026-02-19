import sqlite3

import pandas as pd

from src.config import OUTPUT_DIR, DB_PATH
from src.utils.utils import on_going_messages
from src.generate_sql_lite_db.schema import TABLE_SCHEMA


def _build_create_ddl(table_name: str, columns: dict) -> str:
    """Build a CREATE TABLE DDL statement from the schema column definitions."""
    col_defs = ",\n    ".join(f'"{col}" {dtype}' for col, dtype in columns.items())
    return f'CREATE TABLE "{table_name}" (\n    {col_defs}\n)'


def load_to_db() -> None:
    """
    Carica tutti i CSV di OUTPUT_DIR nel database SQLite DB_PATH.

    Ad ogni invocazione il database viene cancellato e ricreato da zero,
    in modo che rifletta sempre l'ultima generazione di dati.

    Il comportamento per ogni tabella definita in TABLE_SCHEMA è:
        1. Viene creata la tabella con i tipi espliciti dello schema.
        2. Il CSV corrispondente viene letto con pandas.
        3. Le righe vengono inserite con df.to_sql (if_exists='append').
        4. Se il CSV non esiste, la tabella viene comunque creata (vuota)
           e viene stampato un avviso.

    Per aggiungere una nuova tabella è sufficiente aggiungere una voce in
    src/generate_sql_lite_db/schema.py — nessuna modifica a questo file.
    """
    on_going_messages("Loading data into SQLite DB...")

    # Ricrea il DB da zero ad ogni run
    if DB_PATH.exists():
        DB_PATH.unlink()
        on_going_messages("Existing DB removed.")

    conn = sqlite3.connect(DB_PATH)

    try:
        for table_name, definition in TABLE_SCHEMA.items():
            csv_path = OUTPUT_DIR / definition["csv"]
            columns  = definition["columns"]

            # Crea la tabella con lo schema esplicito
            ddl = _build_create_ddl(table_name, columns)
            conn.execute(ddl)

            if not csv_path.exists():
                on_going_messages(f"[WARN] {definition['csv']} not found — table '{table_name}' created empty.")
                continue

            # Legge il CSV e inserisce i dati
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists="append", index=False)
            on_going_messages(f"[OK] '{table_name}' — {len(df):,} rows loaded.")

        conn.commit()

    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"DB load failed: {exc}") from exc

    finally:
        conn.close()

    on_going_messages(f"[OK] DB saved to {DB_PATH}")
