import psycopg2

def audit():
    conn = psycopg2.connect(host='127.0.0.1', port=5432, user='postgres', dbname='carepath')
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"Total tables in 'carepath' DB: {len(tables)}")
    for (tname,) in tables:
        c2 = conn.cursor()
        c2.execute(f'SELECT COUNT(*) FROM "{tname}";')
        cnt = c2.fetchone()[0]
        print(f"  {tname}: {cnt} rows")
    conn.close()

if __name__ == '__main__':
    audit()
