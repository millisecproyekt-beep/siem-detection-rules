import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_URL = os.getenv('SPLUNK_URL')
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN')
QRADAR_URL = os.getenv('QRADAR_URL')
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN')

def sync_splunk():
    print("--- Splunk Yoxlanılır ---")
    path = "splunk/"
    if not os.path.exists(path):
        print(f"XƏTA: '{path}' qovluğu tapılmadı!")
        return
    
    files = [f for f in os.listdir(path) if f.endswith('.json')]
    print(f"Tapılan Splunk faylları: {len(files)}")

    headers = {"Authorization": f"Splunk {SPLUNK_TOKEN}"}
    for filename in files:
        print(f"İşlənir: {filename}...")
        try:
            with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                rule = json.load(f)
                payload = {
                    "name": rule['name'],
                    "search": rule['search'],
                    "is_scheduled": 1,
                    "cron_schedule": rule.get('cron_schedule', '*/15 * * * *'),
                    "output_mode": "json"
                }
                api_url = f"{SPLUNK_URL}/services/saved/searches"
                res = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=10)
                print(f"Nəticə: {res.status_code}")
        except Exception as e:
            print(f"Xəta baş verdi: {e}")

def sync_qradar():
    print("\n--- QRadar Yoxlanılır ---")
    path = "qradar/"
    if not os.path.exists(path):
        print(f"XƏTA: '{path}' qovluğu tapılmadı!")
        return
    
    files = [f for f in os.listdir(path) if f.endswith('.json')]
    print(f"Tapılan QRadar faylları: {len(files)}")

    headers = {"SEC": QRADAR_TOKEN, "Content-Type": "application/json"}
    for filename in files:
        print(f"İşlənir: {filename}...")
        try:
            with open(os.path.join(path, filename), 'r') as f:
                rule = json.load(f)
                res = requests.post(f"{QRADAR_URL}/api/analytics/rules", json=rule, headers=headers, verify=False, timeout=10)
                print(f"Nəticə: {res.status_code}")
        except Exception as e:
            print(f"Xəta baş verdi: {e}")

if __name__ == "__main__":
    sync_splunk()
    sync_qradar()
