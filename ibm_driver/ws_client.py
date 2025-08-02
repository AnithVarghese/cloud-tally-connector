import socketio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.ibmdb2 import get_tables, get_columns, get_table_schema, get_column_data
import sys
import os

# Ensure parent project dir is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from db.ibmdb2 import get_tables, get_columns, get_table_schema, get_column_data

logging.basicConfig(level=logging.DEBUG)
sio = socketio.Client()

@sio.event(namespace="/tunnel")
def connect():
    print("✅ Connected to /tunnel namespace")
    print("🔌 Namespaces connected:", sio.namespaces)

@sio.event(namespace="/tunnel")
def disconnect():
    print("❌ Disconnected from /tunnel namespace")

@sio.on("get_schema", namespace="/tunnel")
def handle_get_schema(data):
    try:
        request_id = data.get("request_id")
        table = data.get("table")
        schema = get_table_schema(table)
        if "/tunnel" in sio.namespaces:
            sio.emit("schema_response", {"request_id": request_id, "schema": schema}, namespace="/tunnel")
        else:
            print("⚠️ Not connected to /tunnel. Skipping schema_response.")
    except Exception as e:
        print("❌ Exception in handle_get_schema:", e)

@sio.on("get_tables", namespace="/tunnel")
def handle_get_tables(data):
    try:
        request_id = data.get("request_id")
        tables = get_tables()
        if "/tunnel" in sio.namespaces:
            sio.emit("tables_response", {"request_id": request_id, "tables": tables}, namespace="/tunnel")
        else:
            print("⚠️ Not connected to /tunnel. Skipping tables_response.")
    except Exception as e:
        print("❌ Exception in handle_get_tables:", e)


@sio.on("get_column_data", namespace="/tunnel")
def handle_get_column_data(data):
    try:
        request_id = data.get("request_id")
        table = data.get("table")
        column = data.get("column")
        values = get_column_data(table, column)
        if "/tunnel" in sio.namespaces:
            sio.emit("column_data_response", {"request_id": request_id, "data": values}, namespace="/tunnel")
        else:
            print("⚠️ Not connected to /tunnel. Skipping column_data_response.")
    except Exception as e:
        print("❌ Exception in handle_get_column_data:", e)

def start_socket():
    try:
        print("🔌 Connecting...")
        sio.connect("https://smartcard-cloud.onrender.com", namespaces=["/tunnel"])
        sio.wait()
    except Exception as e:
        print("❌ Connection failed:", e)