# utils/auth.py

import requests
from config import SMARTCARD_CLOUD


def verify_token(token):
    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]  # safer than replace

        payload = {
            "token": token,
            "client_id": SMARTCARD_CLOUD["client_id"]
        }

        try:
            response = requests.post(SMARTCARD_CLOUD["verify_url"], json=payload)
            print("🌐 Cloud response:", response.status_code, response.text)
            return response.status_code == 200
        except Exception as e:
            print("❌ Error in token verification:", e)
            return False

    except requests.RequestException as req_err:
        print("[Token Verification] Request error:", req_err)
        return False

    except Exception as e:
        print("[Token Verification] General error:", e)
        return False
