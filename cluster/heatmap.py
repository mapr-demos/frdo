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
VOLUME_BASE_PATH='/mapr/frdo/' # top level mount loc of volume for snapshots
RAW_DATA_BASE_PATH = '/tmp/sisenik/' # dir for PP, relative to VOLUME_BASE_PATH 
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


def init_heatmap(snapshot_name):
  client = hiver.connect(HIVE_THRIFT_SERVER_HOST, HIVE_THRIFT_SERVER_PORT)
  current_raw_data_path = RAW_DATA_BASE_PATH
  
  logging.info('Preparing fintrans and heatmap data ingestion ...')

  client.execute('CREATE DATABASE IF NOT EXISTS frdo')
  client.execute('USE frdo')
  client.execute('DROP TABLE IF EXISTS fintrans')
  client.execute('CREATE TABLE fintrans (ts TIMESTAMP, lat STRING, lon STRING, amount STRING, account_id STRING, transaction_id  STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY \'|\'')

  # scan the top-level partition directory for data partitions ...
  try:
    current_raw_data_path = os.path.join(VOLUME_BASE_PATH, '.snapshot', snapshot_name + '/', RAW_DATA_BASE_PATH)
  except:
    pass

  logging.info('- using raw data from %s' %current_raw_data_path) 
  
  partition_dirs = [
    d
    for d in os.listdir(current_raw_data_path)
    if os.path.isdir(os.path.join(current_raw_data_path, d))
    # if re.match(r''\d{4}-\d{2}-/\d{2}', d)
  ]
  
  # ... and load the data into Hive, respectively
  for partition in partition_dirs:
    current_partition = current_raw_data_path + partition
    start_time = datetime.datetime.now()
    client.execute('LOAD DATA LOCAL INPATH \'%s\' INTO TABLE fintrans' %(current_partition))
    end_time = datetime.datetime.now()
    diff_time = end_time - start_time
    logging.info('- loaded raw data from partition %s in %s ms' %(current_partition, diff_time))

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


def heatmap(snapshot_name):
  init_heatmap(snapshot_name) # load the raw data and create tables in Hive
  gen_heatmap() # generate the heatmap data for the app server


def dump_config():
  print(' VOLUME_BASE_PATH:         %s') %VOLUME_BASE_PATH
  print(' RAW_DATA_BASE_PATH:       %s') %RAW_DATA_BASE_PATH
  print(' HEATMAPS_DIR:             %s') %HEATMAPS_DIR
  print(' HIVE_THRIFT_SERVER_HOST:  %s') %HIVE_THRIFT_SERVER_HOST
  print(' HIVE_THRIFT_SERVER_PORT:  %s') %HIVE_THRIFT_SERVER_PORT


def usage():
  print('Usage: python heatmap.py [VOLUME_BASE_PATH] [RAW_DATA_BASE_PATH] [HEATMAPS_DIR] [HIVE_THRIFT_SERVER_HOST] [HIVE_THRIFT_SERVER_PORT] SNAPSHOT_NAME\n')
  print('All parameters besides the SNAPSHOT_NAME are optional and have the following default values:')
  dump_config()
  print('\nExample usage: python heatmap.py /mapr/frdo/ /tmp/sisenik/ ~/frdo/client/heatmaps/ 178.12.154.25 10000 2014-02-03_21-44-30\n')


################################################################################
## Main script

if __name__ == '__main__':
  snapshot_name = ''
  print("="*80)
  try:
    # extract and validate options and their arguments
    opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    
    if len(sys.argv) < 2:
      print('\nYou must provide at least one parameter: the name of the snapshot.\n')
      usage()
      sys.exit(2)
      
    for opt, arg in opts:
      if opt in ('-h', '--help'):
        usage()
        sys.exit()
    try:
      VOLUME_BASE_PATH = args[0]
      RAW_DATA_BASE_PATH = args[1]
      HEATMAPS_DIR = args[2]
      HIVE_THRIFT_SERVER_HOST = args[3]
      HIVE_THRIFT_SERVER_PORT = args[4]
      snapshot_name = args[5]
    except:
      pass
      
    print('\nStarting heatmap generator with the following configuration:')
    dump_config()
    print('Working on snapshot: %s') %snapshot_name
    heatmap(snapshot_name)
  except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)