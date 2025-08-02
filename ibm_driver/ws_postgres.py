import socketio
import logging
from sqlalchemy import create_engine, inspect

DB_URI = "postgresql+psycopg2://postgres:12345@localhost:5432/school"


# Logging setup
logging.basicConfig(level=logging.DEBUG)
sio = socketio.Client()

@sio.event(namespace="/tunnel")
def connect():
    print("✅ PostgreSQL socket connected to /tunnel")

@sio.event(namespace="/tunnel")
def disconnect():
    print("❌ PostgreSQL socket disconnected from /tunnel")

@sio.on("get_postgres_tables", namespace="/tunnel")
def handle_get_postgres_tables(data):
    request_id = data.get("request_id")
    try:
        engine = create_engine(DB_URI)
        inspector = inspect(engine)

        all_tables = []
        for schema in inspector.get_schema_names():
            if schema in ['information_schema', 'pg_catalog']:
                continue
            tables = inspector.get_table_names(schema=schema)
            all_tables.extend([f"{schema}.{table}" for table in tables])

        sio.emit("postgres_tables_response", {
            "request_id": request_id,
            "tables": all_tables
        }, namespace="/tunnel")

    except Exception as e:
        print(f"❌ Error in handle_get_postgres_tables: {e}")
        sio.emit("postgres_tables_response", {
            "request_id": request_id,
            "tables": []
        }, namespace="/tunnel")

@sio.on("get_postgres_schema", namespace="/tunnel")
def handle_get_postgres_schema(data):
    request_id = data.get("request_id")
    full_table_name = data.get("table")  # should be in schema.table format
    try:
        schema, table = full_table_name.split(".")

        engine = create_engine(DB_URI)
        inspector = inspect(engine)
        columns = inspector.get_columns(table, schema=schema)
        column_info = [{"name": col["name"], "type": str(col["type"])} for col in columns]

        sio.emit("postgres_schema_response", {
            "request_id": request_id,
            "schema": column_info
        }, namespace="/tunnel")

    except Exception as e:
        print(f"❌ Error in handle_get_postgres_schema: {e}")
        sio.emit("postgres_schema_response", {
            "request_id": request_id,
            "schema": []
        }, namespace="/tunnel")

def start_socket():
    try:
        print("🔌 PostgreSQL Socket connecting to cloud...")
        sio.connect("https://smartcard-cloud.onrender.com", namespaces=["/tunnel"])
        sio.wait()
    except Exception as e:
        print("❌ PostgreSQL Socket connection failed:", e)
