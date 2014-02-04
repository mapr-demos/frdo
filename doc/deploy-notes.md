# Deployment Notes

## Cluster layout

For a quick demo, I've set up a local cluster using 3 VMs:

    00:50:56:20:05:9B mapr-demo-1 172.16.191.127
    00:50:56:28:AB:E4 mapr-demo-2 172.16.191.126
    00:50:56:2B:28:AB mapr-demo-3 172.16.191.125

And I've installed the services as follows:

    | service    | mapr-demo-1 | mapr-demo-2 | mapr-demo-3 |
    | ---------- | ------------| ------------| ------------|
    | CLDB       |      x      |             |             |
    | ZK         |      x      |      x      |      x      |
    | NFS        |      x      |             |             |
    | Webserver  |             |      x      |             |
    | Fileserver |      x      |      x      |      x      |
    | JT         |             |             |      x      |
    | TT         |      x      |      x      |      x      |
    | Metastore  |             |      x      |             |



## Launch and shutdown

On each node first launch ZK:

    [root@mapr-demo-1 ~]# service mapr-zookeeper start
    [root@mapr-demo-1 ~]# service mapr-zookeeper qstatus
    
First on `mapr-demo-1`, to make sure CLDB master is running, then on all other nodes.

    [root@mapr-demo-1 ~]# service mapr-warden start
    [root@mapr-demo-1 ~]# maprcli node cldbmaster

Finally check if services are running on nodes, as per service layout above:

    [root@mapr-demo-1 ~]# maprcli node list -columns configuredservice,service

To shut down the cluster (again on each node, starting with either 2 or 3):

  [root@mapr-demo-1 ~]# service mapr-warden stop
  [root@mapr-demo-1 ~]# service mapr-zookeeper stop



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

To determine which nodes are running the NFS gateway:

    [root@mapr-demo-1 ~]# maprcli node list -filter "[rp==/*]and[svc==nfs]" -columns id,h,hn,svc, rp
    id                   service                                    hostname     health  ip
    6313779395051377157  tasktracker,cldb,fileserver,nfs,hoststats  mapr-demo-1  0       172.16.191.127



NOTE: currently only `sudo mount -o vers=3,nolock,hard mapr-demo-1:/mapr/MMDemo /mapr` works, check why.


My config:

    [root@mapr-demo-1 /]# cat /opt/mapr/conf/mapr_fstab
    mapr-demo-1:/mapr /mapr vers=3,nolock,hard

Then, mount it (locally and in the cluster):

    [~/tmp] $ sudo mount -o vers=3,nolock,hard mapr-demo-1:/mapr /mapr

Check mounts:

    [root@mapr-demo-1 /] # showmount -e

And get rid of it again:

    [root@mapr-demo-1 /]# umount /mapr

## 3. Install app on cluster

Get the content from both [gess](https://github.com/mhausenblas/gess) and
[FrDO](https://github.com/mhausenblas/frdo). You can either copy locally using
the NFS mount or freshly git clone the repos from one of the nodes into MapR-FS via
a cluster NFS mount.
