USE frdo;

SELECT count(*)
FROM fintrans
WHERE instr(transaction_id, 'xxx') == 1;

