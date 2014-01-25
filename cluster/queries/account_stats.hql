USE frdo;

SELECT count(*) as numtrans, account_id
FROM fintrans
GROUP BY account_id
ORDER BY numtrans;