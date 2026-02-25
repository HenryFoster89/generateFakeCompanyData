SELECT 
    ordinato.OrderID,
    ordinato.RequestedDate,
    ordinato.MaterialID,
    ordinato.CustomerID,
    ordinato.QuantityOrdered,
    venduto.ShipmentDate
FROM 
    ordinato

LEFT JOIN venduto on ordinato.OrderID = venduto.OrderID;



