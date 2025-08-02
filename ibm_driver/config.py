# config.py

import os
from dotenv import load_dotenv
load_dotenv()


DB2_CONFIG = {
    "hostname": os.getenv("DB2_HOSTNAME", "127.0.0.1"),
    "port": os.getenv("DB2_PORT", "50000"),
    "database": os.getenv("DB2_DATABASE", "TESTDB"),
    "username": os.getenv("DB2_USERNAME", "DB2ADMIN"),
    "password": os.getenv("DB2_PASSWORD", "12345"),
}

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "12345",
    "database": "SCHOOL"
}


SMARTCARD_CLOUD = {
    "verify_url": "https://smartcard-cloud.onrender.com/verify-token",
    "client_id": os.getenv("SMARTCARD_CLIENT_ID", "smartcard_client")
}
