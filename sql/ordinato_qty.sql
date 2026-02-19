SELECT MaterialID,
       SUM(QuantityOrdered) AS tot_qty
FROM Ordinato
GROUP BY MaterialID
ORDER BY tot_qty DESC
LIMIT 20;