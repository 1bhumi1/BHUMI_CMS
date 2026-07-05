import sqlite3

def inspect_sqlite():
    db_path = "test_temp.db"
    print(f"Connecting to SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    if "login" in tables:
        cursor.execute("SELECT id, computer_code, password_hash, student_id, staff_id, active FROM login")
        logins = cursor.fetchall()
        print(f"\n--- Logins (Total: {len(logins)}) ---")
        for login in logins:
            print(f"ID: {login[0]} | Code: {login[1]} | Hash: {login[2]} | Student ID: {login[3]} | Staff ID: {login[4]} | Active: {login[5]}")
            
            if login[4]:  # staff_id
                cursor.execute("SELECT first_name, last_name, email FROM staff WHERE id=?", (login[4],))
                staff = cursor.fetchone()
                if staff:
                    print(f"  Staff Name: {staff[0]} {staff[1]} | Email: {staff[2]}")
                
                # Fetch staff roles
                if "staff_role" in tables and "roles" in tables:
                    cursor.execute("""
                        SELECT r.role_type 
                        FROM staff_role sr 
                        JOIN roles r ON sr.role_id = r.id 
                        WHERE sr.staff_id=?
                    """, (login[4],))
                    roles = [r[0] for r in cursor.fetchall()]
                    print(f"  Roles: {roles}")
            elif login[3]:  # student_id
                cursor.execute("SELECT first_name, last_name, email FROM student WHERE id=?", (login[3],))
                student = cursor.fetchone()
                if student:
                    print(f"  Student Name: {student[0]} {student[1]} | Email: {student[2]}")
                    
    conn.close()

if __name__ == "__main__":
    inspect_sqlite()
