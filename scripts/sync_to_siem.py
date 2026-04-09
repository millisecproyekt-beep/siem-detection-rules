import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Secrets
SPLUNK_URL = os.getenv('SPLUNK_URL')
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN')
QRADAR_URL = os.getenv('QRADAR_URL')
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN')

def sync_splunk():
    print("--- Splunk Sinxronizasiyası Başladı ---")
    # ... (Mövcud Splunk kodu bura daxildir) ...

def sync_qradar():
    print("\n--- QRadar Sinxronizasiyası Başladı ---")
    path = "qradar/"
    if not os.path.exists(path): return

    headers = {
        "SEC": QRADAR_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename), 'r') as f:
                rule = json.load(f)
                # QRadar API-na AQL rulu olaraq göndəririk
                response = requests.post(
                    f"{QRADAR_URL}/api/analytics/rules",
                    json=rule,
                    headers=headers,
                    verify=False
                )
                print(f"QRadar Rule: {rule['name']} - Status: {response.status_code}")

if __name__ == "__main__":
    if SPLUNK_TOKEN: sync_splunk()
    if QRADAR_TOKEN: sync_qradar()
