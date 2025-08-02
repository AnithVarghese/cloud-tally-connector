from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from config import DB2_CONFIG
from sqlalchemy import create_engine, inspect, text
import requests
import urllib.parse
from utils.auth import verify_token
from utils.postgres_utils import fetch_postgres_schema
from utils.tally_utils import fetch_companies_ledgers_and_vouchers_from_tally, send_data_to_cloud
from db.ibmdb2 import get_tables, get_columns, get_column_data, get_metadata, get_table_schema, get_all_databases, get_table_preview_data
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # needed for session storage
TALLY_URL = "http://localhost:9000"
# -------------------- API ROUTES --------------------

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/dbs")
def get_dbs():
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"database": DB2_CONFIG['database']})

@app.route("/tables")
def list_tables():
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"tables": get_tables()})

@app.route("/columns")
def list_columns():
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    table = request.args.get("table")
    if not table:
        return jsonify({"error": "Table name required"}), 400
    return jsonify({"columns": get_columns(table)})

@app.route("/listschema/<table>")
def list_schema(table):
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"schema": get_table_schema(table)})

@app.route("/column_data")
def column_data():
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    table = request.args.get("table")
    column = request.args.get("column")
    if not table or not column:
        return jsonify({"error": "Table and column required"}), 400
    return jsonify({"data": get_column_data(table, column)})

@app.route("/metadata")
def full_metadata():
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_metadata())

@app.route("/receive-token", methods=["POST"])
def receive_token():
    data = request.get_json()
    token = data.get("token")
    client_id = data.get("client_id")

    # You can store it or print for testing
    print(f"[📥 Received from cloud] Token: {token}, Client ID: {client_id}")

    # Optional: Save to disk, session, or secure in-memory store
    with open("latest_token.txt", "w") as f:
        f.write(token)

    return jsonify({"status": "received"}), 200

@app.route("/sync-tally", methods=["POST"])
def sync_tally():
    """if "token" not in session:
        return jsonify({"error": "Unauthorized"}), 401"""

    data = fetch_companies_ledgers_and_vouchers_from_tally()
    if data:
        send_data_to_cloud(data)
        return jsonify({"status": "success", "message": "Tally data synced to cloud."})
    else:
        return jsonify({"status": "failed", "message": "Failed to fetch data from Tally"}), 500

@app.route("/query_tally", methods=["POST"])
def query_tally():
    try:
        xml_query = request.json.get("xml")
        if not xml_query:
            return jsonify({"error": "No XML provided"}), 400

        headers = {"Content-Type": "application/xml"}
        response = requests.post(TALLY_URL, data=xml_query, headers=headers)

        return jsonify({
            "status_code": response.status_code,
            "tally_response": response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_ledgers", methods=["GET"])
def get_ledgers():
    xml = f"""<ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export</TALLYREQUEST>
            <TYPE>Collection</TYPE>
            <ID>List of Ledgers</ID>
        </HEADER>
        <BODY>
            <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                <SVCOMPANY>Test Company</SVCOMPANY>
            </STATICVARIABLES>
            </DESC>
        </BODY>
        </ENVELOPE>"""

    try:
        headers = {"Content-Type": "application/xml"}
        response = requests.post(TALLY_URL, data=xml, headers=headers)
        return response.text, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/connect-mysql', methods=['POST'])
def connect_mysql():
    host = request.form['host']
    port = request.form['port']
    username = request.form['username']
    password = request.form['password']
    database = request.form['database']

    # URL encode password
    encoded_pw = urllib.parse.quote_plus(password)

    db_uri = f"mysql+pymysql://{username}:{encoded_pw}@{host}:{port}/{database}"
    
    try:
        engine = create_engine(db_uri)
        inspector = inspect(engine)

        schemas = inspector.get_schema_names()
        result = {}

        for schema in schemas:
            if schema in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                continue
            tables = inspector.get_table_names(schema=schema)
            schema_info = {}
            for table in tables:
                columns = inspector.get_columns(table, schema=schema)
                schema_info[table] = [{"name": col["name"], "type": str(col["type"])} for col in columns]
            result[f"{database}:{schema}"] = schema_info

        # TODO: Sync this result with cloud (send to /receive-mysql endpoint)
        print(f"[MySQL Sync] Extracted schema: {result}")
        # ✅ CLOUD SYNC
        cloud_url = "https://smartcard-cloud.onrender.com/receive-mysql"
        try:
            response = requests.post(cloud_url, json=result)
            print("☁️ Cloud sync response:", response.status_code, response.text)
        except Exception as e:
            print("❌ Failed to sync with cloud:", str(e))


        return redirect('/dashboard')  # or render_template('dashboard.html', ...)
    
    
    except Exception as e:
        return f"Failed to connect to MySQL: {str(e)}"
    


@app.route('/connect-postgres', methods=['POST'])
def connect_postgres():
    host = request.form['host']
    port = request.form['port']
    username = request.form['username']
    password = request.form['password']
    database = request.form['database']

    db_uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

    try:
        engine = create_engine(db_uri)
        inspector = inspect(engine)

        result = {}
        for schema in inspector.get_schema_names():
            if schema in ['information_schema', 'pg_catalog', 'pg_toast']:
                continue
            tables = inspector.get_table_names(schema=schema)
            schema_info = {}
            for table in tables:
                columns = inspector.get_columns(table, schema=schema)
                schema_info[table] = [{"name": col["name"], "type": str(col["type"])} for col in columns]
            result[f"{database}:{schema}"] = schema_info

        # ✅ Send to cloud
        cloud_url = "https://smartcard-cloud.onrender.com/receive-postgres"
        response = requests.post(cloud_url, json=result)
        print("☁️ PostgreSQL Sync Response:", response.status_code, response.text)

        return redirect('/dashboard')

    except Exception as e:
        return f"❌ Failed to connect to PostgreSQL: {str(e)}"

@app.route("/preview-postgres", methods=["POST"])
def preview_postgres():
    dbname = request.form['dbname']
    table_name = request.form['table']  # e.g., public.students

    # Hardcode these for now or extract from session/config if needed
    host = "localhost"
    port = 5432
    user = "postgres"
    password = "12345"
    database = 'school'  # passed from form

    schema_data = fetch_postgres_schema(host, port, user, password, database)
    
    if "error" in schema_data:
        return f"Error fetching schema: {schema_data['error']}", 500

    # Extract formatted schema for the specific table
    try:
        all_tables = schema_data[f"{dbname}:public"]
        columns = all_tables.get(table_name.split(".")[-1], [])
    except Exception as e:
        return f"Invalid schema format: {e}", 500

    return render_template("preview_postgres.html",
                           dbname=dbname,
                           table=table_name,
                           table_info=columns)


# -------------------- HTML ROUTES --------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token")
        try:
            if not token or not verify_token(token):
                return render_template("login.html", error="Invalid token. Please try again.")
        except Exception as e:
            print(f"[ERROR] Token verification failed: {e}")
            return render_template("login.html", error="Error verifying token. Please try again.")
        session["token"] = token
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    token = session.get("token")
    if not token or not verify_token(token):
        return redirect(url_for("login"))

    try:
        databases = get_all_databases()
        synced_dbs = session.get("synced_dbs", [])
        db_tables = {}

        for db in databases:
            try:
                tables = get_tables()
                if not isinstance(tables, list):
                    raise ValueError(f"Expected list of tables, got {type(tables)}")
                db_tables[db] = tables
            except Exception as e:
                print(f"[WARN] Failed to get tables for DB '{db}': {e}")
                db_tables[db] = []  # fallback to empty list

        return render_template("dashboard.html",
                               databases=databases,
                               synced_dbs=synced_dbs,
                               db_tables=db_tables)
    except Exception as e:
        print(f"[ERROR] /dashboard error: {e}")
        return "An error occurred loading the dashboard. Check logs.", 500



@app.route("/sync_db/<db_name>", methods=["POST"])
def sync_database(db_name):
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    
    synced_dbs = session.get("synced_dbs", [])
    if db_name not in synced_dbs:
        synced_dbs.append(db_name)
        session["synced_dbs"] = synced_dbs
    
    return jsonify({"status": "success"})

@app.route("/unsync_db/<db_name>", methods=["POST"])
def unsync_database(db_name):
    token = session.get("token")
    if not token or not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    
    synced_dbs = session.get("synced_dbs", [])
    if db_name in synced_dbs:
        synced_dbs.remove(db_name)
        session["synced_dbs"] = synced_dbs
    
    return jsonify({"status": "success"})



@app.route("/preview/<db>/<tables>")
def preview_data(db, tables):
    token = session.get("token")
    if not token or not verify_token(token):
        return redirect(url_for("login"))
    
    table_list = tables.split(',')
    preview_data = {}
    for table in table_list:
        # Ensure table name is properly formatted (uppercase)
        table_name = table.upper()
        preview_data[table] = get_table_preview_data(table_name)
    
    return render_template("preview.html", tables=table_list, data=preview_data)


if __name__ == "__main__":
    from ws_client import start_socket
    import threading
    from ws_postgres import start_socket as start_postgres_socket
    # Start the WebSocket client in a background thread
    threading.Thread(target=start_socket, daemon=True).start()
    threading.Thread(target=start_postgres_socket, daemon=True).start()
    app.run(port=5005, debug=True)
