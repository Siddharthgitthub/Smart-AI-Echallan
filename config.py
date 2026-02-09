import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Siddharth@10",
        database="smart_echallan"
    )
