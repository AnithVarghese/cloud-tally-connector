import webbrowser
import time
import threading
from app import app  # This imports the Flask app object
from ws_client import start_socket  # If you use WebSocket
import sys
import os

# Ensure the parent directory (project root) is in sys.path so `ibm_driver` is importable
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)




def start_flask():
    # Start WebSocket client in background
    threading.Thread(target=start_socket, daemon=True).start()
    app.run(host="0.0.0.0", port=5005)

# Run Flask app in a thread
threading.Thread(target=start_flask).start()

# Wait a moment for Flask to boot
time.sleep(2)

# Open browser
webbrowser.open("http://localhost:5005/login")
