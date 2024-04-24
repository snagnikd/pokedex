import mysql.connector

dataBase = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    passwd = 'root',
)

# Prepare a cursor object

cursorObject = dataBase.cursor()

cursorObject.execute("CREATE DATABASE crm")