# =============================================================================
# SQLite schema registry
# =============================================================================
# Each entry maps a logical table name to:
#   csv      : filename inside OUTPUT_DIR to read from
#   columns  : ordered dict of  column_name -> SQLite type declaration
#              (PRIMARY KEY, NOT NULL, etc. can be included in the type string)
#
# To add a new table in the future, simply append a new entry here.
# No other file needs to be modified.
#
# SQLite type conventions used:
#   TEXT     : strings and ISO-8601 date/time values  ("YYYY-MM-DD", "YYYY-MM")
#   INTEGER  : whole numbers (quantities, payment terms, etc.)
#   REAL     : floating-point numbers (costs, prices, values)
# =============================================================================

TABLE_SCHEMA: dict[str, dict] = {

    "MasterMaterial": {
        "csv": "MasterMaterial.csv",
        "columns": {
            "MaterialID":    "TEXT PRIMARY KEY",
            "MaterialName":  "TEXT    NOT NULL",
            "Category":      "TEXT    NOT NULL",
            "UnitOfMeasure": "TEXT    NOT NULL",
            "UnitCost":      "REAL    NOT NULL",
            "UnitPrice":     "REAL    NOT NULL",
            "Importance":    "TEXT    NOT NULL",   # imp_1 | imp_2 | imp_3
        },
    },

    "MasterCustomer": {
        "csv": "MasterCustomer.csv",
        "columns": {
            "CustomerID":   "TEXT    PRIMARY KEY",
            "CustomerName": "TEXT    NOT NULL",
            "CustomerType": "TEXT    NOT NULL",
            "Region":       "TEXT    NOT NULL",
            "PaymentTerms": "INTEGER NOT NULL",    # days
        },
    },

    "Ordinato": {
        "csv": "Ordinato.csv",
        "columns": {
            "OrderID":         "TEXT    PRIMARY KEY",
            "OrderDate":       "TEXT    NOT NULL",  # YYYY-MM-DD
            "RequestedDate":   "TEXT    NOT NULL",  # YYYY-MM-DD
            "MaterialID":      "TEXT    NOT NULL",
            "CustomerID":      "TEXT    NOT NULL",
            "QuantityOrdered": "INTEGER NOT NULL",
            "OrderValue":      "REAL    NOT NULL",
        },
    },

    "Venduto": {
        "csv": "Venduto.csv",
        "columns": {
            "SaleID":          "TEXT    PRIMARY KEY",
            "OrderID":         "TEXT    NOT NULL",
            "OrderDate":       "TEXT    NOT NULL",  # YYYY-MM-DD
            "ShipmentDate":    "TEXT    NOT NULL",  # YYYY-MM-DD
            "MaterialID":      "TEXT    NOT NULL",
            "CustomerID":      "TEXT    NOT NULL",
            "QuantityOrdered": "INTEGER NOT NULL",
            "QuantitySold":    "INTEGER NOT NULL",
            "SaleValue":       "REAL    NOT NULL",
        },
    },

    "Budget": {
        "csv": "Budget.csv",
        "columns": {
            "BudgetID":    "TEXT    PRIMARY KEY",
            "BudgetMonth": "TEXT    NOT NULL",      # YYYY-MM
            "MaterialID":  "TEXT    NOT NULL",
            "BudgetQty":   "INTEGER NOT NULL",
            "BudgetValue": "REAL    NOT NULL",
        },
    },

}
