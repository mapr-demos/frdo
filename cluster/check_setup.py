#!/usr/bin/python

"""
Checks Hive setup. 

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2014-03-24
@status: init
"""

import sys
import os
import hiver
import getopt

# for the communication with the Hive Thrift server
HIVE_THRIFT_SERVER_HOST = 'localhost'
HIVE_THRIFT_SERVER_PORT = 10000


def check_setup():
  client = hiver.connect(HIVE_THRIFT_SERVER_HOST, HIVE_THRIFT_SERVER_PORT)
  client.execute('SHOW DATABASES')
  print('All is fine, go ahead and enjoy!')


def usage():
  print('Usage: python check_setup.py HIVE_THRIFT_SERVER_HOST HIVE_THRIFT_SERVER_PORT\n')
  print('\nExample usage: python check_setup.py 178.12.154.25 10000\n')


################################################################################
## Main script

if __name__ == '__main__':
  try:
    opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    
    if len(sys.argv) < 3:
      usage()
      sys.exit(2)
      
    for opt, arg in opts:
      if opt in ('-h', '--help'):
        usage()
        sys.exit()
    try:
      HIVE_THRIFT_SERVER_HOST = args[0]
      HIVE_THRIFT_SERVER_PORT = args[1]
    except:
      pass
      
    check_setup()
  except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)