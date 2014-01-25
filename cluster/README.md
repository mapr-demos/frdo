# FrDO Cluster Description

## Stream processing

In order to process the incoming data stream from `gess`, we need to be able to
do two things:

* **Online part**: applying the fraud detection logic on a sliding window and creating respective alerts
* **Offline part**: make the streams persistent for further batch processing with Hive

Three alternatives were considered: i) a bespoke solution called Sisenik,
ii) Kafka+Samza, and iii) Kafka+Storm. Currently the first option is deployed.

### Sisenik

The name **Sisenik** is a [semordnilap](http://en.wiktionary.org/wiki/semordnilap) 
and hat-tip to [AWS Kinesis](http://aws.amazon.com/kinesis/). 
In fact, Sisenik really is the absolute opposite of Kinesis: it's on-prem, 
runs on a single-node, is single-threaded and by no means production-ready.

Essentially, Sisenik is a sort of `tee` (bash shell command) on steroids.
It splits the incoming data stream, allowing to apply an arbitrarily
 *window function* (in Python) and in parallel writing the data out to disk,
in a partitioned fashion.

#### Online part

Provide your implementation in the `process_window()` function.

#### Offline part

Sisenik's offline part is implemented via the so called persistency partitioner
(PP), configurable via two parameters (in the `sisenik.py` script):

    PP_BASE_DIR = '/tmp/sisenik/' ... the base directory for the persistency partitioner
    PP_TOPLEVEL = '%Y-%m-%d'      ... yields top-level partition ala 2013-11-04/ (that is, per day)
    
Concerning formatting options for `PP_TOPLEVEL` see [strftime.org](http://strftime.org/).

The PP will dump the data in a `|` separated CSV format at a rate of ca. 1MB/sec,
and partition it combining the top-level partitioning scheme and the so called
key range (configurable through `PP_WINDOW_SIZE` in `sisenik.py`) with the following
approximate values:

* `PP_WINDOW_SIZE = 10,000` results in ca. 1MB sized .dat files
* `PP_WINDOW_SIZE = 100,000` results in ca. 10MB sized .dat files
* `PP_WINDOW_SIZE = 1,000,000` results in ca. 100MB sized .dat files

The `$PP_BASE_DIR/$PP_TOPLEVEL` will then be populated with respective .dat files:

    [/tmp/sisenik/2013-12-07] $ ls -alh
    total 74272
    drwxr-xr-x  6 mhausenblas2  wheel   204B  7 Dec 15:59 .
    drwxr-xr-x  4 mhausenblas2  wheel   136B  7 Dec 10:43 ..
    -rw-r--r--  1 mhausenblas2  wheel   9.1M  7 Dec 15:59 2013-12-07T15-58-49-306641_to_2013-12-07T15-58-59-667616.dat
    -rw-r--r--  1 mhausenblas2  wheel   9.1M  7 Dec 15:59 2013-12-07T15-58-59-667719_to_2013-12-07T15-59-10-760215.dat
    -rw-r--r--  1 mhausenblas2  wheel   9.1M  7 Dec 15:59 2013-12-07T15-59-10-760303_to_2013-12-07T15-59-22-061826.dat
    -rw-r--r--  1 mhausenblas2  wheel   9.1M  7 Dec 15:59 2013-12-07T15-59-22-061925_to_2013-12-07T15-59-33-110297.dat
    
    [/tmp/sisenik/2013-12-07] $ head -n 4 2013-12-07T16-46-34-473346_to_2013-12-07T16-46-45-766144.dat
    2013-12-07T16:46:34.473346|41.6722814|1.2743908|100|a881|21cb0bee-5f5f-11e3-82e5-a820664821e3
    2013-12-07T16:46:34.473491|41.6107162|2.2896272|300|a585|21cb117d-5f5f-11e3-b662-a820664821e3
    2013-12-07T16:46:34.473635|36.7220096|-4.4186772|200|a757|21cb1745-5f5f-11e3-bd32-a820664821e3
    2013-12-07T16:46:34.473811|39.7444347|3.429966|300|a883|21cb1e05-5f5f-11e3-8342-a820664821e3    

