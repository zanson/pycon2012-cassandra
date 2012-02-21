import prettyprint
from pycassa.pool import ConnectionPool
from pycassa.columnfamily import ColumnFamily
pool = ConnectionPool('Keyspace1', ['localhost:9160'])
col_fam = ColumnFamily(pool, 'Standard1')

if __name__ == '__main__':
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
    assert('key2' in readData)
    assert(len(readData['key2']) == 1)
    readColumn = readData['key2'][0].column
    assert(readColumn.timestamp == insertTime)
    assert(readColumn.name == 'Column3')
    assert(readColumn.value == 'SomeOtherData')
    assert(readColumn.ttl == None)

#Using Cassandra from the pycassa module

if __name__ == '__main__':
    import pycassa
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

    from pycassa.types import *
    class User(object):
         key = AsciiType()
         name = UTF8Type()
         age = IntegerType()
         height = FloatType()
         score = DoubleType(default=0.0)
         joined = DateType()

    from pycassa.columnfamilymap import ColumnFamilyMap
    cfmap = ColumnFamilyMap(User, pool, 'Standard1')

    from datetime import datetime
    import uuid
    key = str(uuid.uuid4())
    
    user = User()
    user.key = key
    user.name = 'John'
    user.age = 18
    user.height = 5.9
    user.joined = datetime.now()
    cfmap.insert(user)
    
    user = cfmap.get(key=key)
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
    cfmap.remove(user)
    cfmap.get(user.key)
    # cassandra.ttypes.NotFoundException: NotFoundException()
    
#Key Slices
    readData = col_fam.get_range(start='', finish='')
    readData = list(readData)
    print len(readData)
    prettyprint.pp(readData)
    readData = col_fam.get_range(start='', finish='', row_count=2)
    readData = list(readData)
    print len(readData)
    prettyprint.pp(readData)
    readData = col_fam.get_range(start=list(readData)[-1][0], finish='', row_count=2)
    readData = list(readData)
    print len(readData)
    prettyprint.pp(readData)
    readData = col_fam.get_range(start=list(readData)[-1][0], finish='', row_count=2)
    readData = list(readData)
    print len(readData)
    prettyprint.pp(readData)
    readData = col_fam.get_range(start=list(readData)[-1][0], finish='', row_count=2)
    readData = list(readData)
    print len(readData)
    prettyprint.pp(readData)
    readData = col_fam.get_range(start=list(readData)[-1][0], finish='', row_count=2)
    readData = list(readData)
    print len(readData)
    prettyprint.pp(readData)
    
    
    

