# utils/postgres_utils.py
import psycopg2

def fetch_postgres_schema(host, port, user, password, database):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=database
        )
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()

        schema = {}
        for (table_name,) in tables:
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
            """, (table_name,))
            columns = cursor.fetchall()
            schema[table_name] = [{"name": name, "type": dtype} for name, dtype in columns]

        conn.close()
        return {f"{database}:public": schema}
    except Exception as e:
        return {"error": str(e)}
