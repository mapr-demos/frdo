#!/usr/bin/python

"""
Provides the application server for the FrDO WebUI 

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2014-01-25
@status: init
"""

import sys
import os
import logging
import getopt
import urlparse
import urllib
import string
import cgi
import time
import datetime
import json
import socket
import subprocess
import re
import csv

from BaseHTTPServer import BaseHTTPRequestHandler
from os import curdir, pardir, sep

################################################################################
# Config 
DEBUG = False

FRDO_PORT = 6996
CLIENT_DIR = 'webui'
HEATMAPS_DATA = './heatmaps/'
HEATMAP_PREFIX = 'heatmap_'
HEATMAP_EXT = '.tsv'
ALERT_DOC = 'alert.json'


if DEBUG:
  FORMAT = '%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]'
  logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')
else:
  FORMAT = '%(asctime)-0s %(message)s'
  logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')


class FrDOAppServer(BaseHTTPRequestHandler):  
  # reacts to GET request by serving static content in standalone mode 
  # and handles API calls to deal with heatmap data
  def do_GET(self):
    parsed_path = urlparse.urlparse(self.path)
    target_url = parsed_path.path[1:]
    
    if self.path.startswith('/api/'): # API namespace
      self.serve_api(self.path)
    elif self.path == '/':     # static stuff:
      self.serve_static_content('index.html')
    elif self.path.endswith('.ico'):
      self.serve_static_content(target_url, media_type='image/x-icon')
    elif self.path.endswith('.html'):
      self.serve_static_content(target_url, media_type='text/html')
    elif self.path.endswith('.js'):
      self.serve_static_content(target_url, media_type='application/javascript')
    elif self.path.endswith('.css'):
      self.serve_static_content(target_url, media_type='text/css')
    elif self.path.startswith('/img/'):
      if self.path.endswith('.gif'):
        self.serve_static_content(target_url, media_type='image/gif')
      elif self.path.endswith('.png'):
        self.serve_static_content(target_url, media_type='image/png')
      else:
        self.send_error(404,'File Not Found: %s' % target_url)
    else:
      self.send_error(404,'File Not Found: %s' % target_url)
    return
  
  # serves an API call
  def serve_api(self, apicall):
    logging.info('API call: %s ' %(apicall))
    
    # scan heatmaps data directory and serve a list of currently available ones
    if apicall == '/api/heatmap':
      heatmap_files = [
        f.replace(HEATMAP_EXT, '').replace(HEATMAP_PREFIX, '') 
        for f in os.listdir(HEATMAPS_DATA)
        if re.match(r'heatmap.*\.tsv', f)
      ]
      logging.debug('Available heatmaps: %s ' %(heatmap_files))
      self.send_JSON(heatmap_files)
      
    # serve an individual heatmap
    if apicall.startswith('/api/heatmap/'):
      heatmap_filename = apicall[len('/api/heatmap/'):]
      heatmap_filename = ''.join([HEATMAP_PREFIX, heatmap_filename, HEATMAP_EXT])
      heatmap = self.parse_heatmap(HEATMAPS_DATA + heatmap_filename)
      logging.debug('Current heatmap: %s ' %(heatmap))
      self.send_JSON(heatmap)      

    # serve the current alert data
    if apicall == '/api/alerts':
      alerts = self.parse_alerts()
      logging.debug('Current alerts: %s ' %(alerts))
      self.send_JSON(alerts)
      
  
  # parses the TSV format of a heatmap and generates a JSON representation that can be shipped over the wire
  def parse_heatmap(self, heatmap_filename):
    heatmap = []
    with open(heatmap_filename, 'rb') as heatmap_file:
        heatmap_reader = csv.reader(
          heatmap_file,
          delimiter='\t'
        )
        for row in heatmap_reader:
          heatmap.append({'lat': float(row[1]), 'lng': float(row[2]), 'count': int(row[0])})
    return heatmap
  
  # parses the JSON format of the alerts in the recent epoch so that it can be shipped over the wire
  def parse_alerts(self):
    alerts = []
    with open(ALERT_DOC, 'r') as alert_doc:
        alerts = json.load(alert_doc)
    return alerts
  
  # changes the default behavour of logging everything - only in DEBUG mode
  def log_message(self, format, *args):
    if DEBUG:
      try:
        BaseHTTPRequestHandler.log_message(self, format, *args)
      except IOError:
        pass
    else:
      return
  
  # serves static content from file system
  def serve_static_content(self, p, media_type='text/html'):
    logging.debug('path: %s' %(p))
    try:
      f = open(CLIENT_DIR + sep + p) # client static content
      self.send_response(200)
      self.send_header('Content-type', media_type)
      self.end_headers()
      self.wfile.write(f.read())
      f.close()
      return
    except IOError:
      self.send_error(404,'File Not Found: %s' % self.path)
  
  # sends a HTTP response as JSON payload 
  def send_JSON(self, payload):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    logging.debug('Success: %s ' %(payload))
    self.wfile.write(json.dumps(payload))
  

def usage():
  print("Usage: python frdo-client-appserver.py")


################################################################################
## Main script

if __name__ == '__main__':
  print("="*80)
  try:
    # extract and validate options and their arguments
    opts, args = getopt.getopt(sys.argv[1:], 'hv', ['help','verbose'])
    for opt, arg in opts:
      if opt in ('-h', '--help'):
        usage()
        sys.exit()
      elif opt in ('-v', '--verbose'): 
        DEBUG = True
    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('', FRDO_PORT), FrDOAppServer)
    print('\nFrDO app server started, use {Ctrl+C} to shut-down ...')
    print('\nGo to http://localhost:%s/ where the FrDO front-end is served, now.') %(FRDO_PORT)
    server.serve_forever()
  except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2) 
  