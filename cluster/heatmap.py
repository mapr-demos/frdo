#!/usr/bin/python

"""
Generates the heatmap data for the app server. 

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2014-01-25
@status: init
"""

import sys
import os
import logging
import string
import time
import datetime
import json
import re
import csv
import hiver
import getopt
from time import sleep

################################################################################
# configuration

DEBUG = False

# input and output directory settings
RAW_DATA_BASE_PATH = '/tmp/sisenik/' # top-level input (raw) data dir 
HEATMAPS_DIR = '../client/heatmaps/' # output dir

# for the communication with the Hive Thrift server
HIVE_THRIFT_SERVER_HOST = 'localhost'
HIVE_THRIFT_SERVER_PORT = 10000

if DEBUG:
	FORMAT = '%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]'
	logging.basicConfig(level=logging.DEBUG, format=FORMAT, 
datefmt='%Y-%m-%dT%I:%M:%S')
else:
	FORMAT = '%(asctime)-0s %(message)s'
	logging.basicConfig(level=logging.INFO, format=FORMAT, 
datefmt='%Y-%m-%dT%I:%M:%S')


def init_heatmap():
  client = hiver.connect(HIVE_THRIFT_SERVER_HOST, HIVE_THRIFT_SERVER_PORT)

  logging.info('Preparing fintrans and heatmap data ingestion ...')

  client.execute('CREATE DATABASE IF NOT EXISTS frdo')
  client.execute('USE frdo')
  client.execute('DROP TABLE IF EXISTS fintrans')
  client.execute('CREATE TABLE fintrans (ts TIMESTAMP, lat STRING, lon STRING, amount STRING, account_id STRING, transaction_id  STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY \'|\'')

  # scan the top-level partition directory for data partitions ...
  partition_dirs = [
    d
    for d in os.listdir(RAW_DATA_BASE_PATH)
    if os.path.isdir(os.path.join(RAW_DATA_BASE_PATH, d))
    # if re.match(r''\d{4}-\d{2}-/\d{2}', d)
  ]
  # ... and load the data into Hive, respectively
  for partition in partition_dirs:
    snapshot = RAW_DATA_BASE_PATH + partition
    start_time = datetime.datetime.now()
    client.execute('LOAD DATA LOCAL INPATH \'%s\' INTO TABLE fintrans' %(snapshot))
    end_time = datetime.datetime.now()
    diff_time = end_time - start_time
    logging.info('- loaded raw data from %s (in %s)' %(snapshot, diff_time))

  # rebuild the heatmap data table
  start_time = datetime.datetime.now()
  client.execute('DROP TABLE IF EXISTS heatmap')
  client.execute('CREATE TABLE heatmap AS SELECT count(*) as numtrans, lat, lon FROM fintrans GROUP BY lat, lon ORDER BY numtrans')
  end_time = datetime.datetime.now()
  diff_time = end_time - start_time
  logging.info('- created heatmap data (in %s)' %(diff_time))


def gen_heatmap():
  client = hiver.connect(HIVE_THRIFT_SERVER_HOST, HIVE_THRIFT_SERVER_PORT)
  client.execute('USE frdo')
  client.execute('SELECT * FROM heatmap')
  rows = client.fetchAll()
  
  heatmap_file_name = ''.join(['heatmap_', datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), '.tsv'])
  heatmap_file_name = os.path.abspath(
          ''.join([HEATMAPS_DIR, heatmap_file_name])
  )
  heatmap_file  = open(heatmap_file_name, 'wb')
  heatmap_file_writer = csv.writer(
      heatmap_file,
      delimiter='\t',
  )
  for row in rows:
    fields = row.split('\t')
    logging.debug('%s' %(row))
    row = [fields[0], fields[1], fields[2]]
    heatmap_file_writer.writerow(row)
  logging.info('Generated heatmap at %s' %(heatmap_file_name))


def heatmap():
  init_heatmap() # load the raw data and create tables in Hive
  gen_heatmap() # generate the heatmap data for the app server


def dump_config():
  print(' RAW_DATA_BASE_PATH:      %s') %RAW_DATA_BASE_PATH
  print(' HEATMAPS_DIR:            %s') %HEATMAPS_DIR
  print(' HIVE_THRIFT_SERVER_HOST: %s') %HIVE_THRIFT_SERVER_HOST
  print(' HIVE_THRIFT_SERVER_PORT: %s') %HIVE_THRIFT_SERVER_PORT


def usage():
  print('Usage: python heatmap.py [RAW_DATA_BASE_PATH] [HEATMAPS_DIR] [HIVE_THRIFT_SERVER_HOST] [HIVE_THRIFT_SERVER_PORT]\n')
  print('All parameters are optional and have the following default values:')
  dump_config()
  print('\nExample usage: python heatmap.py /data/sisenik/ ~/frdo/client/heatmaps/ 178.12.154.25 10000\n')


################################################################################
## Main script

if __name__ == '__main__':
  print("="*80)
  try:
    # extract and validate options and their arguments
    opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    for opt, arg in opts:
      if opt in ('-h', '--help'):
        usage()
        sys.exit()
    try:
      RAW_DATA_BASE_PATH = args[0]
      HEATMAPS_DIR = args[1]
      HIVE_THRIFT_SERVER_HOST = args[2]
      HIVE_THRIFT_SERVER_PORT = args[3]
    except:
      pass
      
    print('\nStarting heatmap generator with the following configuration:')
    dump_config()
    heatmap()
  except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)