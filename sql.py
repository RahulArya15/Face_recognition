import textwrap
import pyodbc
#specifies the driver
driver = 'ODBC Driver 18 for SQL Server'

#specify the server name and database name
server_name='attendancebyface'
database_name='attendance'

#create a server string
server = '{server_name}.database.windows.net,1433' .format(server_name=server_name)

#define username and password
username = "rahul"
password = "Attendance@123"

#create the full connection string.
connection_string = textwrap.dedent('''
    Driver={driver};
    Server={server};
    Database={database};
    Uid={username};
    Pwd={password};
    Encrypt=yes;
    TrustServerCertificate=no;
    Connection Timeout=30;
'''.format(
    driver=driver,
    server=server,
    database=database_name,
    username=username,
    password=password,
)
)

#create new PYODBC connection object

cnxn: pyodbc.Connection = pyodbc.connect(connection_string)

cnxn.autocommit = True
#create a new cursor object from connection
crsr : pyodbc.Cursor = cnxn.cursor()

#defining insert query
insert_sql="INSERT INTO Persons (name) VALUES( ?)"

#define record sets
 
records=[
    ('rahul',),
    ('Obama',)
]
#Execute insert statement
crsr.executemany(insert_sql, records)

#commiting
crsr.commit()

#define a select query
select_sql="Select * From Persons"

#execute the select query
crsr.execute(select_sql)

#grab the data
print(crsr.fetchall())

#closing connection
cnxn.close()