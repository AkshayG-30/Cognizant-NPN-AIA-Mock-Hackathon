import psycopg2

def setup_user():
    conn = psycopg2.connect(host='127.0.0.1', port=5432, user='postgres', dbname='carepath')
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check/Create user carepath
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname='carepath'")
    if not cur.fetchone():
        cur.execute("CREATE USER carepath WITH PASSWORD 'carepath_dev' SUPERUSER;")
        print("Created user carepath with superuser privileges")
    else:
        cur.execute("ALTER USER carepath WITH PASSWORD 'carepath_dev' SUPERUSER;")
        print("Updated user carepath with password and superuser privileges")
        
    cur.execute("GRANT ALL PRIVILEGES ON DATABASE carepath TO carepath;")
    cur.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO carepath;")
    cur.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO carepath;")
    print("Granted all privileges on database carepath to user carepath")
    conn.close()

if __name__ == '__main__':
    setup_user()
