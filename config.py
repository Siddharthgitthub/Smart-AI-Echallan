import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="${{RAILWAY_PRIVATE_DOMAIN}}",
        user="root",
        password="JnwFbtCIsGEeRRHVntGuuArwCeqQzIJI",
        database="railway",
        port=3306
    )
    return conn


