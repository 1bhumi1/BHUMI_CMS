import pymysql

passwords = ["rootpassword", "root", "", "admin", "password"]
for pwd in passwords:
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            user="root",
            password=pwd,
            database="campus_active"
        )
        print(f"SUCCESS: Connected to MySQL with user 'root' and password '{pwd}'")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        print("Tables:", cursor.fetchall())
        conn.close()
        break
    except Exception as e:
        print(f"FAILED: Connection with password '{pwd}' failed: {e}")
