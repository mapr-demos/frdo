#!/usr/bin/python

""" 
  The implementation of the online alert part consuming data from gess.

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2014-01-25
@status: init
"""
import sys
import os
import socket
import logging
import string
import datetime
import random
import uuid
import json
import re
import csv
from collections import deque

DEBUG = False

# a dev flag, can disable the offline part
DO_OFFLINE = True

# defines the host where a single gess is expected to run
GESS_IP = "127.0.0.1"

# defines the port to listen for
GESS_UDP_PORT = 6900

# defines the buffer size (in Bytes) of the datagram receiver
BUFFER_SIZE = 1024 

# defines the window size for processing and determines
# also the file size of a single partition (one .dat file)
# 10,000    ... 1MB 
# 100,000   ... 10MB
# 1,000,000 ... 100MB
PP_WINDOW_SIZE = 100000


################################################################################
#
# Below the configuration of the persistency partitioner (PP) that takes 
# care of storing the incoming data stream on disk, using configurable
# partitions (top-level and key-range). 

# the base directory for the persistency partitioner
# NOTE: if you set that to empty, the data will be persisted 
#       in a sub-directory of the current working directory
PP_BASE_DIR = '/tmp/sisenik/'

# the top-level partitioning for the persistency partitioner (per day)
PP_TOPLEVEL = '%Y-%m-%d' # yields top-level partition ala 2013-11-04/

if DEBUG:
  FORMAT = '%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]'
  logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')
else:
  FORMAT = '%(message)s'
  logging.basicConfig(level=logging.INFO, format=FORMAT)


# implements a very naive fraud detction, just look for the flag 'xxx'
def process_window(fintran):
    transaction_id = fintran['transaction_id']
    if transaction_id.startswith('xxx'):
      account_id = fintran['account_id']
      logging.info('DETECTED fraudulent transaction on account %s' %(account_id))

def run():
  in_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # use UDP
  in_socket.bind((GESS_IP, GESS_UDP_PORT))
  pp_window = deque(maxlen=PP_WINDOW_SIZE) # sliding window for transactions 
  ticks = 0 # ticks (virtual time basis for window)
  
  while True:
    ticks += 1 # advance the virtual time
    
    # receive one transaction via UDP and add to processing window
    data, addr = in_socket.recvfrom(BUFFER_SIZE)
    logging.debug('%s' %data)
    fintran = json.loads(data) # parse raw data into dictionary
    timestamp = re.sub(r':|\.', '-', fintran['timestamp']) # convert from format 2013-11-08T10:58:19.668225 to 2013-11-08T10-58-19-668225  
    pp_window.append(fintran) # put transaction into queue
    
    ############################################################################
    # the online stream processing part
    # 
    process_window(fintran)
    
    ############################################################################
    # the offline part: persistency partitioner (PP).
    # stores the incoming data stream on disk, using configurable
    # partitions (using top-level and key-range)
    
    if DO_OFFLINE:
      if ticks == 1: # first financial transaction in the queue
        start_key = timestamp
        logging.info('Starting new partition at key %s' %start_key)
    
      if ticks == PP_WINDOW_SIZE: # the queue is full
        end_key = timestamp
        logging.info('Closing partition from key %s to %s' %(start_key, end_key))
        # create partition for keyrange and dump content:
        top_level_partition = datetime.datetime.now().strftime(PP_TOPLEVEL)
        top_level_partition_full = os.path.abspath(
          ''.join([PP_BASE_DIR, top_level_partition, '/'])
        )
        # create a new directory per top-level partition:
        if not os.path.exists(top_level_partition_full):
            os.makedirs(top_level_partition_full)
            logging.info('Creating new top-level partition %s' %top_level_partition_full)
      
        # write out the data partition (in | separated CSV format):
        partition_file_name = ''.join([start_key, '_to_', end_key, '.dat'])
        partition_file_name = os.path.abspath(
                ''.join([top_level_partition_full, '/', partition_file_name])
        )
        partition_file  = open(partition_file_name, 'wb')
        partition_file_writer = csv.writer(
            partition_file,
            delimiter='|',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        start_time = datetime.datetime.now()
        for ft in pp_window:
          hive_timestamp = ft['timestamp'].replace('T', ' ')
          row = [hive_timestamp, ft['lat'], ft['lon'], ft['amount'], ft['account_id'], ft['transaction_id']]
          partition_file_writer.writerow(row)
        end_time = datetime.datetime.now() 
        diff_time = end_time - start_time 
        logging.info('Written partition %s in %d ms' %(partition_file_name, diff_time.microseconds/1000))
        partition_file.close()
        pp_window =  deque(maxlen=PP_WINDOW_SIZE)
        ticks = 0


################################################################################
## Main script

if __name__ == '__main__':
  run()