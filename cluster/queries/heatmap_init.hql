CREATE DATABASE IF NOT EXISTS frdo;

USE frdo;

DROP TABLE IF EXISTS fintrans;

CREATE TABLE fintrans (
 ts TIMESTAMP,
 lat STRING,
 lon STRING,
 amount STRING,
 account_id STRING,
 transaction_id  STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '|';

LOAD DATA LOCAL INPATH '/private/tmp/sisenik/2013-12-07' INTO TABLE fintrans;

DROP TABLE IF EXISTS heatmap;
 
CREATE TABLE heatmap AS
SELECT count(*) as numtrans, lat, lon
FROM fintrans 
GROUP BY lat, lon
ORDER BY numtrans;