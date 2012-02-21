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

From the Apache Cassandra project:  
[http://cassandra.apache.org/](http://cassandra.apache.org/)  

    $ wget http://apache-mirror-site/apache-cassandra-1.0.7.tar.gz
    $ tar xzf apache-cassandra-1.0.7.tar.gz
    $ cd apache-cassandra-1.0.7

Or DataStax hosts some Debian and RedHat packages:  
[http://www.datastax.com/docs/1.0/install/install_package](http://www.datastax.com/docs/1.0/install/install_package)

# How do I run it?  

- Edit cassandra.yaml  
	- Change data/commit log locations (default /var/cassandra/data and /var/cassandra/commitlog)  
- Edit log4j-server.properties  
	- Change the log location/levels (default /var/log/cassandra/system.log)  

### Start the server  
    $ cd apache-cassandra-1.0.7/bin
    $ ./cassandra

# Setup tips for local instances  

- Rename the cassandra.yaml and log4j-server.properties to be templates  
- Change the "cassandra" script to run them through sed  

Add something like the following to set the folders to be under the install folder.  

    if [ ! -f "$CASSANDRA_CONF/cassandra.yaml" ]; then
        echo "Generating Config File: $CASSANDRA_CONF/cassandra.yaml \
        from $CASSANDRA_CONF/cassandra.yaml.in"
        MYDIR="$( cd "${CASSANDRA_HOME}" && pwd )"
        sed "s#\${CASSANDRA_HOME}#${MYDIR}#g" \
        $CASSANDRA_CONF/cassandra.yaml.in > $CASSANDRA_CONF/cassandra.yaml
        sed "s#\${CASSANDRA_HOME}#${MYDIR}#g" \
        $CASSANDRA_CONF/log4j-server.properties.in > $CASSANDRA_CONF/log4j-server.properties
    fi

# First create a "Table"  

Use the Cassandra CLI to setup a keyspace and column family to hold our data

    $ cd apache-cassandra-1.0.7/bin
    $ ./cassandra-cli
    [default@unknown] connect localhost/9160;
    Connected to: "Test Cluster" on localhost/9160
    [default@unknown] create keyspace Keyspace1
    ...	    with placement_strategy = 'org.apache.cassandra.locator.SimpleStrategy'
    ...	    and strategy_options = [{replication_factor:1}];
    [default@unknown] use Keyspace1;
    [default@Keyspace1] create column family Standard1
    ...	    and comparator = 'AsciiType';

# Installing the Cassandra module  

### Thrift
Generate it yourself if you have thrift installed:  

    $ cd apache-cassandra-1.0.7/interface
    $ thrift --gen py --out=whereitgoes cassandra.thrift
    $ python -c "import whereitgoes.cassandra.constants"

### Pycassa (or Thrift)
Install pycassa, and use it from there:  

    $ pip install pycassa
    $ python -c "import pycassa.cassandra.c10.constants"

# Using Cassandra Thrift vs Pycassa  

{% left %}
### Thrift  

    from thrift.transport import TSocket
    from thrift.transport import TTransport
    from thrift.protocol import TBinaryProtocol
    from pycassa.cassandra.c10 import Cassandra
    from pycassa.cassandra.c10 import ttypes

{% end %}

{% right %}
### Pycassa  

    from pycassa.pool import ConnectionPool
    from pycassa.columnfamily import ColumnFamily

{% end %}

# Connecting  
{% left %}
### Thrift  

    socket =
      TSocket.TSocket('localhost', 9160)
    transport =
      TTransport.TFramedTransport(socket)
    protocol =
      TBinaryProtocol.
        TBinaryProtocolAccelerated(transport)
    client =
      Cassandra.Client(protocol)
    transport.open()
    client.set_keyspace('Keyspace1')

{% end %}

{% right %}
### Pycassa  

    pool =
      ConnectionPool('Keyspace1',
                     ['localhost:9160'])
    col_fam =
      ColumnFamily(pool,
                   'Standard1')

{% end %}

# Writing  
{% left %}
### Thrift  

    import time
    insertTime = long(time.time()*1e6)
    dataToInsert =
      {'key1': {'Standard1': 
                  [ttypes.Mutation(
                     ttypes.ColumnOrSuperColumn(
                       ttypes.Column(
                         name='Column1',
                         value='SomeData',
                         timestamp=insertTime,
                         ttl=None)))]}}
    client.batch_mutate(
      mutation_map=
        dataToInsert,
      consistency_level=
        ttypes.ConsistencyLevel.QUORUM)

{% end %}

{% right %}
### Pycassa  

    col_fam.insert(
      'key1',
      {'Column1':
         'PycassaData'})

{% end %}

# Reading  
{% left %}
### Thrift  

    readData = client.multiget_slice(
      keys=set(['key1']),
      column_parent=
        ttypes.ColumnParent(
          column_family='Standard1'),
      predicate=
        ttypes.SlicePredicate(
          column_names=['Column1']),
      consistency_level=
        ttypes.ConsistencyLevel.QUORUM)

{% end %}

{% right %}
### Pycassa  

    readData = col_fam.get(
      'key1',
      columns=['Column1'])

{% end %}

# Deleting  

### Pycassa  

    col_fam.remove('key1', ['Column2'])
    col_fam.remove('key2')

# Batch operations  

### Pycassa  

    col_fam.batch_insert({'key4': {'Column1': 'PycassaData4', 
                                   'Column2': 'PycassaData5',
                                   'Column3': 'PycassaData6',
                                   'Column4': 'PycassaData7',
                                   'Column5': 'PycassaData8'},
                          'key5': {'Column7': 'PycassaData9'}})

### Or  

    b = cf.batch(queue_size=10)
    b.insert('key1', {'Column1':'value11', 'Column2':'value21'})
    b.insert('key2', {'Column1':'value12', 'Column2':'value22'}, ttl=15)
    b.remove('key1', ['Column2'])
    b.remove('key2')
    b.send()
    
    readData = col_fam.multiget(['key1', 'key2', 'key3', 'key4', 'key5'])
    readData = col_fam.multiget(['key3', 'key4', 'key5'], columns=['Column1', 'Column7'])


# Column Slices  

### Pycassa  

    readData = col_fam.get('key4', column_start='Column2', column_finish='Column4')
    readData = col_fam.get('key4', column_reversed=True, column_count=3)    

# Types  

	import pycassa.types

# Column Family Mapper

    from pycassa.types import *
    class User(object):
         key = LexicalUUIDType()
         name = Utf8Type()
         age = IntegerType()
         height = FloatType()
         score = DoubleType(default=0.0)
         joined = DateType()

    from pycassa.columnfamilymap import ColumnFamilyMap
    cfmap = ColumnFamilyMap(User, pool, 'users')

# Inserting using the mapper

    from datetime import datetime
    import uuid
    key = uuid.uuid4()
    
    user = User()
    user.key = key
    user.name = 'John'
    user.age = 18
    user.height = 5.9
    user.joined = datetime.now()
    cfmap.insert(user)    

# Getting it back out

    user = cfmap.get(key)
    print user.name
    # "John"
    print user.age
    # 18
    users = cfmap.multiget([key1, key2])
    print users[0].name
    # "John"
    for user in cfmap.get_range():
        print user.name
    # "John"
    # "Bob"
    # "Alex"

# Deleting

    cfmap.remove(user)
    cfmap.get(user.key)
    # cassandra.ttypes.NotFoundException: NotFoundException()

# Using Composite Columns  

- [Schema Design](http://www.datastax.com/dev/blog/schema-in-cassandra-1-1)

# Indexing in Cassandra  

- [Native secondary indexes][dsBlog] [Documentation @ DataStax][dsDocs]  
- Roll your own with wide rows  
- Composite Columns  

[dsBlog]: http://www.datastax.com/dev/blog/whats-new-cassandra-07-secondary-indexes  
[dsDocs]: http://www.datastax.com/docs/1.0/ddl/indexes  

# Some links about indexing  

- [Blog post going through some options.](http://www.anuff.com/2011/02/indexing-in-cassandra.html)  
- [Presentation on indexing.](http://www.slideshare.net/edanuff/indexing-in-cassandra)
- [Another blog post describing different patterns for indexing.](http://pkghosh.wordpress.com/2011/03/02/cassandra-secondary-index-patterns/)  

# Native Indexes  

- Easy to use.  
- Let you use filtering queries.  
- Usually fine as long as the indexed column is not under constant load.  
- Not recommended for high cardinality values (i.e. timestamps, birth dates, keywords, etc.)  
	- More performant if the indexed column doesn't have a lot of different values.  
- Make writes slower to indexed columns (read before write)  

# Rolling your own  

- Have to take care of removing changed values yourself.  
- If you know the new value doesn't exists, no read before write (faster).  
- Can design the index to return needed information so that it becomes a denomalized query, not just an index.  
- Can use things like composite columns, and other tricks to allow range like searches.  
- Can index in other ways then just column values.  

# Lessons Learned

- Use indexes.  Don't iterate over keys.  
- When you come up with a new query, come up with a schema to service it quickly.  
- Don't be afraid to write your data to multiple places.  
	-  Batch insert is your friend.  
- Run repair.  
- Don't let your free disk space fall under the size of your largest column family.  
- Key cache and row cache are nice, but having your files fit in the Linux OS disk cache is beter.  


