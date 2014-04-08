#!/bin/sh

/mapr/MapR-Cluster/frdo/cluster/frdo.sh down
sleep 2
killall python
sleep 1
killall frdo.sh
sleep 1
hive -f /mapr/MapR-Cluster/frdo/cluster/queries/all_reset.hql 
sleep 1
rm -Rf /mapr/MapR-Cluster/frdo/tmp/sisenik/*
rm -Rf /mapr/MapR-Cluster/frdo/client/heatmaps/*
rm -Rf /mapr/MapR-Cluster/frdo/cluster/*.pid
rm -Rf /mapr/MapR-Cluster/frdo/client/alert*