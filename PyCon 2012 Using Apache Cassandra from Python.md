Title: PyCon 2012 Using Apache Cassandra from Python  
Subtitle: Jeremiah Jordan, Morningstar, Inc. http://www.morningstar.com  
Author: Jeremiah Jordan  
Company: Morningstar, Inc. http://www.morningstar.com  
Email: jeremiah.jordan@morningstar.com  
Twitter: @jeremiahdjordan  
presdate: 2012-03-14  
footer-top-right: Morningstar, Inc. http://www.morningstar.com  
footer-bottom-left: @jeremiahdjordan  
footer-bottom-right: jeremiah.jordan@morningstar.com  

# What is Apache Cassandra
  
A very brief introduction to Apache Cassandra:  
  
- Column based key-value store (multi-level dictionary)  
- Combination of [Dynamo (Amazon)][dynamo] and [BigTable (Google)][bigtable]  
- Schema-optional  

"Cassandra is a highly scalable, eventually consistent, distributed, structured key-value store. Cassandra brings together the distributed systems technologies from [Dynamo][dynamo]  and the data model from Google's [BigTable][bigtable]. Like Dynamo, Cassandra is eventually consistent. Like BigTable, Cassandra provides a ColumnFamily-based data model richer than typical key/value systems." From the [Cassandra Wiki](http://wiki.apache.org/cassandra/ "Cassandra Wiki")

[dynamo]: http://s3.amazonaws.com/AllThingsDistributed/sosp/amazon-dynamo-sosp2007.pdf "Amazon Dynamo Paper"  
[bigtable]: http://labs.google.com/papers/bigtable-osdi06.pdf "Google BigTable Paper"

# Where do I get it?  

From the Apache Cassandra project: [http://cassandra.apache.org/](http://cassandra.apache.org/)  

    $ wget http://apache-mirror-site/apache-cassandra-1.0.6.tar.gz
    $ tar xzf apache-cassandra-1.0.6.tar.gz
    $ cd apache-cassandra-1.0.6

Or DataStax hosts some Debian and RedHat packages:
[http://www.datastax.com/docs/1.0/install/install_package](http://www.datastax.com/docs/1.0/install/install_package)

# How do I run it?
- Edit cassandra.yaml  to change data/commit log locations from /var/cassandra/data and /var/cassandra/commitlog
- Edit log4j-server.properties to change log the syslog location (default /var/log/cassandra/system.log)

    $ cd apache-cassandra-1.0.6/bin
    $ ./cassandra

For unit testing, I usually move the cassandra.yaml and log4j-server.properties for be .in templates, and change the "cassandra" script to run those through sed  

    if [ ! -f "$CASSANDRA_CONF/cassandra.yaml" ]; then
        echo "Generating Config File: $CASSANDRA_CONF/cassandra.yaml from $CASSANDRA_CONF/cassandra.yaml.in"
        MYDIR="$( cd "${CASSANDRA_HOME}" && pwd )"
        sed "s#\${CASSANDRA_HOME}#${MYDIR}#g" $CASSANDRA_CONF/cassandra.yaml.in > $CASSANDRA_CONF/cassandra.yaml
        sed "s#\${CASSANDRA_HOME}#${MYDIR}#g" $CASSANDRA_CONF/log4j-server.properties.in > $CASSANDRA_CONF/log4j-server.properties
    fi

# First create a "Table"
Use the Cassandra CLI to setup a keyspace and column family to hold our data

    $ cd apache-cassandra-1.0.6/bin
    $ ./cassandra-cli
    Welcome to Cassandra CLI version 1.0.6
    
    Type 'help;' or '?' for help.
    Type 'quit;' or 'exit;' to quit.
    
    [default@unknown] connect localhost/9160;
    Connected to: "Test Cluster" on localhost/9160
    
    [default@unknown] create keyspace Keyspace1
    ...	    with placement_strategy = 'org.apache.cassandra.locator.SimpleStrategy'
    ...	    and strategy_options = {replication_factor:1};
    ebf7f200-31f1-11e1-0000-242d50cf1fbf
    Waiting for schema agreement...
    ... schemas agree across the cluster
    
    [default@unknown] use Keyspace1;
    Authenticated to keyspace: Keyspace1
    
    [default@Keyspace2] create column family Standard1
    ...	    and comparator = 'AsciiType';
    69064210-31f2-11e1-0000-242d50cf1fbf
    Waiting for schema agreement...
    ... schemas agree across the cluster

#Installing the Cassandra thrift API module
You can either generate it yourself if you have thrift installed:  

    $ cd apache-cassandra-1.0.7/interface
    $ thrift --gen py --out=whereitgoes cassandra.thrift
    $python -c "import whereitgoes.cassandra.constants;print whereitgoes.cassandra.constants.VERSION"
    19.20.0

or install pycassa, and use it from there:  

    $ pip install pycassa
    $ python -c "import pycassa.cassandra.c10.constants;print pycassa.cassandra.c10.constants.VERSION"
    19.18.0

#Using Cassandra from the thrift API

    from thrift.transport import TSocket, TTransport
    from thrift.protocol import TBinaryProtocol
    from pycassa.cassandra.c10 import Cassandra
    from pycassa.cassandra.c10 import ttypes

#Connecting

    socket = TSocket.TSocket('localhost', 9160)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocolAccelerated(transport)
    client = Cassandra.Client(protocol)
    transport.open()
    client.set_keyspace('Keyspace1')

#Writing

    import time
    insertTime = long(time.time()*1e6)
    dataToInsert = {'key1': {'Standard1': [ttypes.Mutation(
                                            ttypes.ColumnOrSuperColumn(
                                                ttypes.Column(name='Column1',
                                                              value='SomeData',
                                                              timestamp=insertTime,
                                                              ttl=None)))]}}
    client.batch_mutate(mutation_map=dataToInsert,
                        consistency_level=ttypes.ConsistencyLevel.QUORUM)

#Reading

    readData = client.multiget_slice(keys=set(['key1']),
                                     column_parent=ttypes.ColumnParent(
                                        column_family='Standard1'),
                                     predicate=ttypes.SlicePredicate(
                                        column_names=['Column1']),
                                     consistency_level=ttypes.ConsistencyLevel.QUORUM)
    assert('key1' in readData)
    assert(len(readData['key1']) == 1)
    readColumn = readData['key1'][0].column
    assert(readColumn.timestamp == insertTime)
    assert(readColumn.name == 'Column1')
    assert(readColumn.value == 'SomeData')
    assert(readColumn.ttl == None)

#Batch operations

    dataToInsert = {'key1': {'Standard1': [ttypes.Mutation(
                                            ttypes.ColumnOrSuperColumn(
                                                ttypes.Column(name='Column2',
                                                              value='SomeMoreData',
                                                              timestamp=insertTime,
                                                              ttl=None)))]},
                    'key2': {'Standard1': [ttypes.Mutation(
                                            ttypes.ColumnOrSuperColumn(
                                                ttypes.Column(name='Column3',
                                                              value='SomeOtherData',
                                                              timestamp=insertTime,
                                                              ttl=None)))]}}
    client.batch_mutate(mutation_map=dataToInsert,
                        consistency_level=ttypes.ConsistencyLevel.QUORUM)

    readData = client.multiget_slice(keys=set(['key1', 'key2']),
                                     column_parent=ttypes.ColumnParent(
                                        column_family='Standard1'),
                                     predicate=ttypes.SlicePredicate(
                                        column_names=['Column1',
                                                      'Column2',
                                                      'Column3']),
                                     consistency_level=ttypes.ConsistencyLevel.QUORUM)

#Installing the pycassa module

    pip install pycassa

#Using Cassandra from the pycassa module

    from pycassa.pool import ConnectionPool
    from pycassa.columnfamily import ColumnFamily

#Connecting

    pool = ConnectionPool('Keyspace1', ['localhost:9160'])
    col_fam = ColumnFamily(pool, 'Standard1')

#Writing

    col_fam.insert('key3', {'Column4': 'PycassaData'})

#Reading

    readData = col_fam.get('key3')    
    col_fam.insert('key3', {'Column5':'PycassaData2', 'Column6':'PycassaData3'})
    readData = col_fam.get('key3')
    
#Batch operations

    col_fam.batch_insert({'key4': {'Column1': 'PycassaData4', 
                                   'Column2': 'PycassaData5',
                                   'Column3': 'PycassaData6',
                                   'Column4': 'PycassaData7',
                                   'Column5': 'PycassaData8'},
                          'key5': {'Column7': 'PycassaData9'}})
    readData = col_fam.multiget(['key3', 'key4', 'key5'])
    readData = col_fam.multiget(['key3', 'key4', 'key5'], columns=['Column1', 'Column7'])

#Column Slices

    readData = col_fam.get('key4', column_start='Column2', column_finish='Column4')
    readData = col_fam.get('key4', column_reversed=True, column_count=3)    

#Types

- Column Family Mapper
- Auto type conversion

#Using Composite Columns

- Fun fun fun
- [Schema Design](http://www.datastax.com/dev/blog/schema-in-cassandra-1-1)

#Indexing in Cassandra

- [Native secondary indexes][datastaxIndexes] [Documentation](http://www.datastax.com/docs/1.0/ddl/indexes)  
- Roll your own with wide rows  
- Composite Columns  
- [Blog Post on this stuff][anuff]  
- [Presentation on Indexing](http://www.slideshare.net/edanuff/indexing-in-cassandra)
- [Another Post](http://pkghosh.wordpress.com/2011/03/02/cassandra-secondary-index-patterns/)  

[datastaxIndexes]:http://www.datastax.com/dev/blog/whats-new-cassandra-07-secondary-indexes  
[anuff]: http://www.anuff.com/2011/02/indexing-in-cassandra.html  

#Native vs Rolling your own

- Native  
	- Easy to use.  
	- Let you use filtering queries.  
	- Not recommended for high cardinality values (i.e. timestamps, birth dates, keywords, etc.)  
		- More performant if the indexed column doesn't have a lot of different values.  
	- Make writes slower to indexed columns (read before write)  
	- Usually fine as long as the indexed column is not under constant load.  
- Rolling your own  
	- Have to take care of removing changed values yourself.  
	- If you know the new value doesn't exists, no read before write (faster).  
	- Can design the index to return needed information so that it becomes a denomalized query, not just an index.  
	- Can use things like composite columns, and other tricks to allow range like searches.  
	- Can index in other ways then just column values.  

#Setting up native indexes

	abc def g

#How to use them from pycassa

	col_fam.get_indexed

#Lessons Learned

- Use indexes.  Don't iterate over keys.  
- When you come up with a new query, come up with a schema to service it quickly.  
- Don't be afraid to write your data to multiple places.  
	-  Batch insert is your friend.  
- Run repair.  
- Don't let your free disk space fall under the size of your largest column family.  
- Key cache and row cache are nice, but having your files fit in the Linux OS disk cache is beter.  


