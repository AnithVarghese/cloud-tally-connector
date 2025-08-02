import os
os.add_dll_directory(r"C:\Program Files\IBM\SQLLIB_01\BIN")
import ibm_db
from config import DB2_CONFIG

def connect_db():
    conn_str = (
        f"DATABASE={DB2_CONFIG['database']};"
        f"HOSTNAME={DB2_CONFIG['hostname']};"
        f"PORT={DB2_CONFIG['port']};"
        f"PROTOCOL=TCPIP;"
        f"UID={DB2_CONFIG['username']};"
        f"PWD={DB2_CONFIG['password']};"
    )
    return ibm_db.connect(conn_str, "", "")

def get_tables():
    conn = connect_db()
    tables = []
    stmt = ibm_db.tables(conn, None, DB2_CONFIG['username'].upper(), None, "TABLE")
    result = ibm_db.fetch_assoc(stmt)
    while result:
        tables.append(result["TABLE_NAME"])
        result = ibm_db.fetch_assoc(stmt)
    ibm_db.close(conn)
    return tables

def get_columns(table, conn=None):
    external_conn = conn is not None
    if not conn:
        conn = connect_db()
    columns = []
    query = f"""
        SELECT COLNAME, TYPENAME, LENGTH
        FROM SYSCAT.COLUMNS
        WHERE TABNAME = '{table.upper()}'
        AND TABSCHEMA = '{DB2_CONFIG['username'].upper()}'
    """
    stmt = ibm_db.exec_immediate(conn, query)
    result = ibm_db.fetch_assoc(stmt)
    while result:
        columns.append({
            "name": result["COLNAME"],
            "type": result["TYPENAME"],
            "length": result["LENGTH"]
        })
        result = ibm_db.fetch_assoc(stmt)
    if not external_conn:
        ibm_db.close(conn)
    return columns

def get_column_data(table, column):
    conn = connect_db()
    query = f"SELECT {column} FROM {table}"
    stmt = ibm_db.exec_immediate(conn, query)
    values = []
    row = ibm_db.fetch_assoc(stmt)
    while row:
        values.append(row[column.upper()])
        row = ibm_db.fetch_assoc(stmt)
    ibm_db.close(conn)
    return values

def get_table_schema(table):
    conn = connect_db()
    stmt = ibm_db.columns(conn, None, DB2_CONFIG['username'].upper(), table.upper())
    schema = []
    result = ibm_db.fetch_assoc(stmt)
    while result:
        schema.append({
            "name": result["COLUMN_NAME"],
            "type": result["TYPE_NAME"]
        })
        result = ibm_db.fetch_assoc(stmt)
    ibm_db.close(conn)
    return schema

def get_metadata():
    conn = connect_db()
    tables_stmt = ibm_db.tables(conn, None, DB2_CONFIG['username'].upper(), None, "TABLE")
    tables = []
    result = ibm_db.fetch_assoc(tables_stmt)
    while result:
        table_name = result["TABLE_NAME"]
        columns = get_columns(table_name, conn)  # reuse existing connection
        tables.append({"name": table_name, "columns": columns})
        result = ibm_db.fetch_assoc(tables_stmt)

    stmt = ibm_db.exec_immediate(conn, "SELECT CURRENT SERVER FROM SYSIBM.SYSDUMMY1")
    db_name = ibm_db.fetch_tuple(stmt)[0]
    ibm_db.close(conn)
    return {"database": db_name, "tables": tables}

def get_table_preview_data(table, limit=10):
    conn = connect_db()
    # Fetch column names
    col_stmt = ibm_db.exec_immediate(conn, f"SELECT * FROM {table} FETCH FIRST 1 ROWS ONLY")
    num_cols = ibm_db.num_fields(col_stmt)
    columns = [ibm_db.field_name(col_stmt, i) for i in range(num_cols)]

    # Fetch data rows
    stmt = ibm_db.exec_immediate(conn, f"SELECT * FROM {table} FETCH FIRST {limit} ROWS ONLY")
    rows = []
    row = ibm_db.fetch_assoc(stmt)
    while row:
        rows.append([row.get(col.upper()) for col in columns])
        row = ibm_db.fetch_assoc(stmt)

    ibm_db.close(conn)
    return {"columns": columns, "rows": rows}


def get_all_databases():
    conn = connect_db()
    try:
        # Get the current database
        stmt = ibm_db.exec_immediate(conn, "SELECT CURRENT SERVER FROM SYSIBM.SYSDUMMY1")
        current_db = ibm_db.fetch_tuple(stmt)[0]
        
        # In IBM DB2, we can only connect to one database at a time
        # So we'll return the current database as a list
        return [current_db]
    finally:
        ibm_db.close(conn)

