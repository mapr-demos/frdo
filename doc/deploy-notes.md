# Deployment Notes

## Plan

1. Install Hive
1. Mount `/mapr` locally
1. Install demo software on cluster

## 1. Install Hive

On one node:

    yum install mapr-hivemetastore

And on this node also edit `/opt/mapr/conf/env.sh`:

    export JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk-1.7.0.9.x86_64/jre
    export HIVE_HOME=/opt/mapr/hive/hive-0.12


## 2. Mount MapR-FS locally

    sudo mount $IP_ADDRESS_OF_CLUSTER_NODE:/mapr /mapr


## 3. Install app on cluster

Get the content from both [gess](https://github.com/mhausenblas/gess) and
[FrDO](https://github.com/mhausenblas/frdo). You can either copy locally using
the NFS mount or freshly git clone the repos from one of the nodes into MapR-FS via
a cluster NFS mount.
