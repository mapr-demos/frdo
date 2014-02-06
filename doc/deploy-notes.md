# Deployment notes

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



## Launch and shutdown the cluster

On each node first launch ZK:

    [root@mapr-demo-1 ~]# service mapr-zookeeper start
    [root@mapr-demo-1 ~]# service mapr-zookeeper qstatus
    
First on `mapr-demo-1`, to make sure CLDB master is running, then on all other nodes.

    [root@mapr-demo-1 ~]# service mapr-warden start
    [root@mapr-demo-1 ~]# maprcli node cldbmaster
    cldbmaster
    ServerID: 6313779395051377157 HostName: mapr-demo-1

Finally check if services are running on nodes, as per service layout above:

    [root@mapr-demo-1 ~]# maprcli node list -columns configuredservice,service
    service                                                                  hostname     configuredservice                                                                 ip
    tasktracker,cldb,fileserver,nfs,hoststats                                mapr-demo-1  tasktracker,cldb,fileserver,nfs,hoststats                                         172.16.191.127
    fileserver,oozie,tasktracker,beeswax,webserver,hoststats,hue,jobtracker  mapr-demo-2  fileserver,hivemeta,oozie,tasktracker,beeswax,webserver,hoststats,hue,jobtracker  172.16.191.126
    fileserver,httpfs,tasktracker,hoststats                                  mapr-demo-3  fileserver,oozie,httpfs,tasktracker,beeswax,hoststats,hue,jobtracker              172.16.191.125

To shut down the cluster (again on each node, starting with either 2 or 3):

  [root@mapr-demo-1 ~]# service mapr-warden stop
  [root@mapr-demo-1 ~]# service mapr-zookeeper stop


## Install dependencies and app

1. Install Hive and Hiver
1. Prepare a volume for app
1. Mount `/mapr`
1. Install demo software on cluster

### 1. Install Hive and Hiver

On one node, say `mapr-demo-2`, install Hive and the Metastore (note: only works
with Metastore not HiveServer2, for now, so if you have installed this, 
deactivate it):

    [root@mapr-demo-2 ~]# yum install mapr-hivemetastore

And further, on this node (`mapr-demo-2`) edit `/opt/mapr/conf/env.sh` to:

    export JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk-1.7.0.9.x86_64/jre

Then `su mapr` and add this to `~/.bashrc`, needed for the Hive and the 
[Hiver](https://github.com/tebeka/hiver) Python module:

    export HIVE_HOME=/opt/mapr/hive/hive-0.12
    export PYTHONPATH=$PYTHONPATH:$HIVE_HOME/lib/py

... and apply changes:

    [mapr@mapr-demo-2 ~]$ source ~/.bashrc

Now it's time to install the Hiver Python module:

    [mapr@mapr-demo-2 ~]$ cd /tmp
    [mapr@mapr-demo-2 tmp]$ git clone https://github.com/tebeka/hiver
    [mapr@mapr-demo-2 tmp]$ cd hiver
    [mapr@mapr-demo-2 tmp]$ python ./setup.py install

... and check if it works:

    [mapr@mapr-demo-2 tmp]$ echo 'import hiver' | python

If you see no output here this means good news here. Otherwise, make sure you're
using the right version of [Thrift for Python](http://thrift.apache.org/docs/BuildingFromSource/);
you might need to build it from source.


### 2. Prepare a volume for app

To hold the raw data and also to serve the app, you need to create a 
[volume](http://doc.mapr.com/display/MapR/Managing+Data+with+Volumes) as so:

    [root@mapr-demo-1 /] # maprcli volume create -name frdo -path /frdo -mount true

This creates a volume called `frdo` and mounts it at `/mapr/frdo`. To check how
the volume is doing you can use the following command:

    [root@mapr-demo-1 /] # maprcli volume info -name frdo -json

    
### 3. Mount MapR-FS

To determine which nodes are running the NFS gateway:

    [root@mapr-demo-1 ~]# maprcli node list -filter "[rp==/*]and[svc==nfs]" -columns id,h,hn,svc, rp
    id                   service                                    hostname     health  ip
    6313779395051377157  tasktracker,cldb,fileserver,nfs,hoststats  mapr-demo-1  0       172.16.191.127

My config (to make mount permanent):

    [root@mapr-demo-1 /]# cat /opt/mapr/conf/mapr_fstab
    mapr-demo-1:/mapr /mapr vers=3,nolock,hard

To manually mount it (locally and in the cluster, as loopback):

    [~/tmp] $ sudo mount -o vers=3,nolock,hard mapr-demo-1:/mapr /mapr

NOTE: currently only `sudo mount -o vers=3,nolock,hard mapr-demo-1:/mapr/MMDemo /mapr` works, check why.

To check mounts use:

    [root@mapr-demo-1 /] # showmount -e

And get rid of it again (after the demo):

    [root@mapr-demo-1 /]# umount /mapr


### 4. Install app on cluster

Get the content from both [gess](https://github.com/mhausenblas/gess) and
[FrDO](https://github.com/mhausenblas/frdo). You can either copy locally using
the NFS mount or freshly git clone the repos from one of the nodes into MapR-FS via
a cluster NFS mount.

Once you have everything downloaded, you might need to change settings in 
[frdo.sh](../cluster/frdo.sh) to adapt paths such as the FrDO volume mount path
or the gess install path to your environment.