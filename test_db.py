# test_db.py
import psycopg2

try:
    conn = psycopg2.connect(
        host="127.0.0.1", database="femcare", user="nat", password="123456naty1."
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {str(e)}")
