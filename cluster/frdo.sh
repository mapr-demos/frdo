#!/bin/bash -

################################################################################
# 
# This is the FrDO launch script allowing you to start or stop the demo. 
# It launches the following services and apps:
# 
#  * the data generator for synthetic streams called gess, 
#    see https://github.com/mhausenblas/gess
#  * the stream processing part called sisenik (for persistent partitions 
#    and online alerts, see cluster/README.md for details)
#  * the heatmap generator, and
#  * last but not least the application server that serves the heatmap and
#    alerts data as well as the UI in the browser, which is available via:
#    http://localhost:6996/
# 
# Depending on your setup you'll need to set the paths to the respective
# components in the below sections
#
# NOTE that in order for this script to work, two preconditions must be met:
#
#   1. Hadoop (HDFS) must be runnin: start-all.sh
#   2. Hive server is running and accessible: hive --service hiveserver
#
# Usage: ./frdo.sh
#

SISENIK_PID=sisenik.pid

################################################################################
# CONFIG 

############## SYSTEM ##############

# Hive
HIVE_THRIFT_SERVER_HOST=localhost
HIVE_THRIFT_SERVER_PORT=10000

# MapR
FRDO_DATA_VOLUME=frdo

############## APPLICATION ##############

# gess config
GESS_DIR=../../gess/
GESS_SCRIPT=./gess.sh
GESS_IP=127.0.0.1 # on which node of the cluster gess runs

# sisenik config
SISENIK_SCRIPT=sisenik.py
SISENIK_PP=/tmp/sisenik/ # top-level input (raw) data dir 
HEATMAPS_DIR=../client/heatmaps/ # directory where the heatmaps go
ALERT_DOC=../client/alert.json # file where the alerts go

# heatmap generator config
HEATMAP_SCRIPT=heatmap.py

# application and web server config
APP_SERVER_DIR=../client/
APP_SERVER_SCRIPT=frdo-client-appserver.py

################################################################################

function usage() {
	printf "Usage: %s up | down | snap | gen | run\n" $0
}

function launch_frdo() {
  echo 'Starting up FrDO:'
  cur_dir=$PWD
  cd $GESS_DIR
  $GESS_SCRIPT start
  cd $cur_dir
  start_sisenik $1 $2 $3
}

function shutdown_frdo() {
  echo 'Shutting down FrDO:'
  cur_dir=$PWD
  cd $GESS_DIR
  $GESS_SCRIPT stop
  cd $cur_dir
  stop_sisenik
  # ... as well as clean up the nohup stuff
  if [ -f nohup.out ]; then
    rm nohup.out
  fi
}

function start_sisenik() {
  nohup python $SISENIK_SCRIPT $1 $2 $3 &
  echo $! > $SISENIK_PID
}

function stop_sisenik() {
  # try to find the PID of sisenik process and kill it
  if [ -f $SISENIK_PID ]; then
    if kill -0 `cat $SISENIK_PID` > /dev/null 2>&1; then
      echo 'Shutting down sisenik ...'
      kill `cat $SISENIK_PID`
      rm $SISENIK_PID
    fi
  fi
}

function gen_heatmap() {

  echo "Press [CTRL+C] to stop heatmap generation."

  while true
  do
    # create a snapshot ...
    snapshot_name=$(date +"%Y-%m-%d_%H-%M-%S")
    maprcli volume snapshot create -snapshotname $snapshot_name -volume $5
  
    # ... and then, after waiting 2 sec, just to be sure, generate the
    #    heatmap on the snapshotted directory
    sleep 2
    snapshot_name=2014-02-03_21-44-30
    python $HEATMAP_SCRIPT $1 $2 $3 $4 $snapshot_name
  done
}

function serve_app() {
  cur_dir=$PWD
  cd $APP_SERVER_DIR
  python $APP_SERVER_SCRIPT
}

###############################################################################
# main script
#
# sequence is: 'up' then 'gen' in one terminal and 'run' in another
case $1 in
 up )      launch_frdo $GESS_IP $SISENIK_PP $ALERT_DOC ;;
 down )    shutdown_frdo ;;
 gen )     gen_heatmap $SISENIK_PP $HEATMAPS_DIR $HIVE_THRIFT_SERVER_HOST $HIVE_THRIFT_SERVER_PORT $FRDO_DATA_VOLUME ;;
 run )     serve_app ;;
 * )       usage ; exit 1 ; ;;
esac