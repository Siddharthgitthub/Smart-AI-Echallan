import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
username TEXT,
password TEXT,
role TEXT
)
""")

cur.execute("""
INSERT INTO users(name,username,password,role)
VALUES('Admin','admin','admin123','admin')
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS challans(
id INTEGER PRIMARY KEY AUTOINCREMENT,
vehicle_no TEXT,
owner_name TEXT,
violation TEXT,
fine INTEGER,
status TEXT,
date TEXT
)
""")

conn.commit()
conn.close()

print("Database ready")
