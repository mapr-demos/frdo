# Fraud Detection Online (FrDO) Demo

This demo is about fraud detection in the realm of financial transactions.
The goal is to demonstrate how to identify fraudulent ATM withdrawals in Europe.
The rate of the incoming data stream is around 10,000 financial transactions, 
with a throughput of ca. 2MB/sec, resulting in some 7GB of log data per hour.
A fraudulent ATM withdrawal in the context of this demo is defined as any
sequence of consecutive withdrawals from the same account, in different locations.
The underlying ATM location data stems from the [OpenStreetMap](http://openstreetmap.org) project.

## Installation

### Dependencies

* MapR [M5 Enterprise Edition for Apache Hadoop](http://www.mapr.com/products/mapr-editions/m5-edition)
* Python 2.7+
* [heatmap.js](http://www.patrick-wied.at/static/heatmapjs/) for the WebUI (included in the client lib)
* cluster of three or more physical or virtual machines (local sandbox or cloud deployment in GCE or EC2)

### Deployment

## Usage

In the following, I describe the exact steps necessary to execute the demo.

### STEP 1: producing data

To demonstrate the data producing part of the demo, you first want to launch
the streaming data generator gess:

    [mapr@hp-mapr-4 gess]$ ./gess.sh start

Then, you launch Sisenik (for online processing and persistent partitioning):

    [mapr@hp-mapr-4 cluster]$ pwd
    /mapr/HPMapR/demo/frdo/cluster
    [mapr@hp-mapr-4 cluster]$ python sisenik.py

In order to have some data to work with, let gess+Sisenik run for a while 
(some minutes). In the default configuration, Sisenik dumps some 1MB/sec, that
is, say, for a 3 minutes run you'll end up with some 180MB (=`3 x 60 x 1MB/s`) 
worth of data.

While Sisenik is running, show the console where it is running. You should see
something like the following (online alerts and partitioning status):

    Starting new partition at key 2013-12-08T15-44-09-609910
    DETECTED fraudulent transaction on account a22
    DETECTED fraudulent transaction on account a764
    DETECTED fraudulent transaction on account a863
    Closing partition from key 2013-12-08T15-44-09-609910 to 2013-12-08T15-44-19-167569
    Written partition /tmp/sisenik/2013-12-08/2013-12-08T15-44-09-609910_to_2013-12-08T15-44-19-167569.dat in 885 ms
    Starting new partition at key 2013-12-08T15-44-19-167666
    DETECTED fraudulent transaction on account a799
    DETECTED fraudulent transaction on account a461
    DETECTED fraudulent transaction on account a185
    Closing partition from key 2013-12-08T15-44-19-167666 to 2013-12-08T15-44-29-519752
    Written partition /tmp/sisenik/2013-12-08/2013-12-08T15-44-19-167666_to_2013-12-08T15-44-29-519752.dat in 804 ms

To stop producing data, first kill Sisenik (CTRL+C) and then shut down gess:

    [mapr@hp-mapr-4 gess]$ ./gess.sh stop

Now it's time to generate the heatmap data for the app server. To this end,
make sure the Hive Thrift server is running:

    [mapr@hp-mapr-4 demo]$ $ hive --service hiveserver

Then you launch the heatmap generator script like so:

    [mapr@hp-mapr-4 cluster]$ python heatmap.py
    2013-12-08T03:51:42 Preparing fintrans and heatmap data ingestion ...
    2013-12-08T03:51:53 - loaded raw data from /tmp/sisenik/2013-12-08 (in 0:00:01.210577)
    2013-12-08T03:52:15 - created heatmap data (in 0:00:22.185298)
    2013-12-08T03:52:16 Generated heatmap at ../frdo/client/heatmaps/heatmap_2013-12-08_15-52-16.tsv

The new heatmap data is now available for the app server to serve to the Web UI.

### STEP 2: consuming data

To demo the consumption part you first have to launch the FrDo app server:

    [client] $ python frdo-client-appserver.py
    ================================================================================

    FrDO app server started, use {Ctrl+C} to shut-down ...
    2013-12-08T04:10:56 API call: /api/heatmap/test
    2013-12-08T04:10:56 API call: /api/heatmap
    2013-12-08T04:10:56 Heatmaps: ['2013-12-07_22-10-03', '2013-12-08_06-02-29', '2013-12-08_09-03-41', '2013-12-08_15-52-16']


Leave the app server running as long as you're showing the client part: for this,
simply launch a Web browser (tested under Chrome); you should then see the FrDO WebUI:

![FrDO WebUI screen shot](doc/frdo-webui-screenshot.png?raw=true)

Hit the `refresh` button to step through the different heatmap files.

That's it. 

## Architecture

FrDO consists of two parts, the cluster part and the client part.

Cluster part:

* The source of the financial transactions is [gess](https://github.com/mhausenblas/gess).
* For handling online alerts and creating persistent partitions of the data a script called Sisenik is used.
* Hive and MapR snapshots are used to compute the heat-map data.

See more details in the [cluster documentation](cluster/README.md).

Client part:

* Online alerts are available via the command line (console of one of the cluster machines).
* The [app server](frdo/client/frdo-client-appserver.py) serves static resources and a JSON representation of the heatmap data.


![FrDO architecture](doc/frdo-architecture.png?raw=true)

See also the [architecture diagram](doc/frdo-architecture.pdf) as PDF.

## Data

The streaming data is generated by [gess](https://github.com/mhausenblas/gess) in
the following form:

    ...
    {
      'timestamp': '2013-11-08T10:58:19.668225', 
      'lat': '36.7220096',
      'lon': '-4.4186772',
      'amount': 100, 
      'account_id': 'a335', 
      'transaction_id': '636adacc-49d2-11e3-a3d1-a820664821e3'
    }
    ...

Once processed by Sisenik, the TSV data on disk is of the following shape:

    ...
    2013-12-07T16:46:34.473346|41.6722814|1.2743908|100|a881|21cb0bee-5f5f-11e3-82e5-a820664821e3
    2013-12-07T16:46:34.473491|41.6107162|2.2896272|300|a585|21cb117d-5f5f-11e3-b662-a820664821e3
    2013-12-07T16:46:34.473635|36.7220096|-4.4186772|200|a757|21cb1745-5f5f-11e3-bd32-a820664821e3
    2013-12-07T16:46:34.473811|39.7444347|3.429966|300|a883|21cb1e05-5f5f-11e3-8342-a820664821e3 
    ...


## Comparison with vanilla Hadoop-based solution

In order to realise this app with vanilla Hadoop/HDFS/Hive, one would need
something like [Apache Kafka](http://kafka.apache.org/) to handle the incoming data
stream and partitioning. We do this here with a simple Pythonscript (`sisenik.py`)
that has less than 150 LOC and this is only possible because MapRFS is a fully read/write,
POSIX compliant filesystem. Same is true for the app server, another Python script (`frdo-client-appserver.py`)
that runs directly against the mounted cluster filesystem which in the vanilla Hadoop
case would likely be realized via special connectors or exporting the resulting heat-maps.


## License

All software in this repository is available under [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0.html)
and all other artifacts such as documentation or figures (drawings) are
available under [CC BY 3.0](http://creativecommons.org/licenses/by/3.0/).