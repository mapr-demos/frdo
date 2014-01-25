USE frdo;

SELECT count(*) as numtrans, lat, lon
FROM fintrans 
GROUP BY lat, lon
ORDER BY numtrans;
