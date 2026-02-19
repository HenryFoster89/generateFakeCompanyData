-- ============================================================
-- Vista: vw_SalesVsBudget
-- Granularità: Mese x Materiale
-- Nota: il Budget è definito a livello Mese+Materiale.
--       Le vendite vengono aggregate alla stessa granularità.
-- Utilizzo: SELECT * FROM vw_SalesVsBudget ORDER BY Month, MaterialID;
-- ============================================================

DROP VIEW IF EXISTS vw_SalesVsBudget;

CREATE VIEW vw_SalesVsBudget AS

WITH sales_by_month AS (
    SELECT
        strftime('%Y-%m', ShipmentDate) AS Month,
        MaterialID,
        SUM(QuantitySold)               AS ActualQty,
        SUM(SaleValue)                  AS ActualValue
    FROM Venduto
    GROUP BY
        strftime('%Y-%m', ShipmentDate),
        MaterialID
),

budget_by_month AS (
    SELECT
        BudgetMonth                     AS Month,
        MaterialID,
        SUM(BudgetQty)                  AS BudgetQty,
        SUM(BudgetValue)                AS BudgetValue
    FROM Budget
    GROUP BY
        BudgetMonth,
        MaterialID
),

-- FULL OUTER JOIN emulato in SQLite:
-- parte 1 → tutte le vendite + eventuale budget
-- parte 2 → budget senza vendite corrispondenti
combined AS (
    SELECT
        COALESCE(s.Month,      b.Month)      AS Month,
        COALESCE(s.MaterialID, b.MaterialID) AS MaterialID,
        s.ActualQty,
        s.ActualValue,
        b.BudgetQty,
        b.BudgetValue
    FROM sales_by_month   s
    LEFT JOIN budget_by_month b
           ON s.Month       = b.Month
          AND s.MaterialID  = b.MaterialID

    UNION ALL

    SELECT
        b.Month,
        b.MaterialID,
        NULL  AS ActualQty,
        NULL  AS ActualValue,
        b.BudgetQty,
        b.BudgetValue
    FROM budget_by_month  b
    LEFT JOIN sales_by_month s
           ON b.Month      = s.Month
          AND b.MaterialID = s.MaterialID
    WHERE s.MaterialID IS NULL      -- solo mesi/materiali senza vendite
)

SELECT
    c.Month,

    -- Anagrafica Materiale
    c.MaterialID,
    m.MaterialName,
    m.Category,
    m.UnitOfMeasure,
    m.Importance,

    -- Consuntivo (venduto)
    c.ActualQty,
    ROUND(c.ActualValue,  2)                                        AS ActualValue,

    -- Budget
    c.BudgetQty,
    ROUND(c.BudgetValue,  2)                                        AS BudgetValue,

    -- Delta assoluto
    ROUND(c.ActualQty   - c.BudgetQty,   2)                        AS DeltaQty,
    ROUND(c.ActualValue - c.BudgetValue, 2)                        AS DeltaValue,

    -- % di raggiungimento budget
    CASE WHEN c.BudgetQty   > 0
         THEN ROUND(c.ActualQty   * 100.0 / c.BudgetQty,   1)
    END                                                             AS PctQtyAttainment,
    CASE WHEN c.BudgetValue > 0
         THEN ROUND(c.ActualValue * 100.0 / c.BudgetValue, 1)
    END                                                             AS PctValueAttainment

FROM combined c
LEFT JOIN MasterMaterial  m  ON c.MaterialID = m.MaterialID;
