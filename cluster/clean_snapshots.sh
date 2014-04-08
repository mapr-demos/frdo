#!/bin/sh

rm -Rf /mapr/MapR-Cluster/frdo/cluster/snapshots-vol-frdo.txt
cd /mapr/MapR-Cluster/frdo/.snapshot
folders=$(ls)
echo "$folders" > /mapr/MapR-Cluster/frdo/cluster/snapshots-vol-frdo.txt
sleep 30
for f in $folders
do
	maprcli volume snapshot remove -volume frdo -snapshotname $f
	echo "Removing snapshot name : $f"
done