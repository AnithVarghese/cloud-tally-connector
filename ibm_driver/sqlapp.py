from flask import Flask, jsonify
from sqlalchemy import create_engine, inspect, text

app = Flask(__name__)

DB_URIS = {
    'test_mysql_db': 'mysql+pymysql://root:12345@localhost:3306/test_mysql_db'
}


# 🔧 Create engine for each database
engines = {db: create_engine(uri) for db, uri in DB_URIS.items()}

def get_engine(dbname):
    """Return an engine for the given database name."""
    if dbname in engines:
        return engines[dbname]
    for engine in engines.values():
        try:
            with engine.connect() as conn:
                if 'mysql' in str(engine.url):
                    conn.execute(f'USE {dbname}')
                return engine
        except:
            continue
    return None

@app.route('/')
def home():
    return "Hello Flask is working!"

@app.route('/api/data/<dbname>/<tablename>/<columnname>')
def get_column_data(dbname, tablename, columnname):
    engine = get_engine(dbname)
    if not engine:
        return jsonify({'error': 'Database not found'}), 404
    try:
        with engine.connect() as conn:
            if 'mysql' in str(engine.url):
                query = f"SELECT `{columnname}` FROM `{dbname}`.`{tablename}` LIMIT 100"
            else:
                query = f'SELECT "{columnname}" FROM "{dbname}"."{tablename}" LIMIT 100'
            result = conn.execute(text(query)).mappings().all()
            return jsonify([dict(row) for row in result])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/schema/table')
def schema_table():
    system_schemas = {'information_schema', 'mysql', 'performance_schema', 'sys'}
    result = {}
    for dbname, engine in engines.items():
        try:
            inspector = inspect(engine)
            schemas = inspector.get_schema_names()
            for schema in schemas:
                if schema in system_schemas:
                    continue  # Skip system schemas
                tables = inspector.get_table_names(schema=schema)
                schema_info = {}
                for table in tables:
                    columns = inspector.get_columns(table, schema=schema)
                    schema_info[table] = [
                        {"name": col["name"], "type": str(col["type"])} for col in columns
                    ]
                result[f'{dbname}:{schema}'] = schema_info
        except Exception as e:
            result[dbname] = {"error": str(e)}
    return jsonify(result)



@app.route('/listtable/<dbname>')
def list_tables(dbname):
    engine = get_engine(dbname)
    if not engine:
        return jsonify({'error': 'Database not found'}), 404
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema=dbname)
        return jsonify(tables)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/listcolumns/<dbname>/<tablename>/')
def list_columns(dbname, tablename):
    engine = get_engine(dbname)
    if not engine:
        return jsonify({'error': 'Database not found'}), 404
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(tablename, schema=dbname)
        return jsonify([col['name'] for col in columns])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/previewdata/<dbname>/<tablename>')
def preview_data(dbname, tablename):
    engine = get_engine(dbname)
    if not engine:
        return jsonify({'error': 'Database not found'}), 404
    try:
        with engine.connect() as conn:
            if 'mysql' in str(engine.url):
                query = f"SELECT * FROM `{dbname}`.`{tablename}` LIMIT 10"
            else:
                query = f'SELECT * FROM "{dbname}"."{tablename}" LIMIT 10'
            result = conn.execute(text(query)).mappings().all()
            return jsonify([dict(row) for row in result])

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
