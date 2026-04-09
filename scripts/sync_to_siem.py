import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


SPLUNK_URL = os.getenv('SPLUNK_URL', '').strip()
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()
QRADAR_URL = os.getenv('QRADAR_URL', '').strip()
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

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
    print(f"\n--- QRadar Yoxlanılır (v27.0): {QRADAR_URL} ---")
    path = "qradar/"
    if not os.path.exists(path): return
    
    # Version 27.0 üçün xüsusi tənzimlənmiş headers
    headers = {
        "SEC": QRADAR_TOKEN, 
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "27.0" # Sənin API Documentation-da gördüyün rəqəm
    }
    
    for filename in [f for f in os.listdir(path) if f.endswith('.json')]:
        with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
            rule = json.load(f)
            try:
                # URL-in təmiz olduğundan əmin oluruq
                clean_url = QRADAR_URL.rstrip('/')
                api_url = f"{clean_url}/api/analytics/rules"
                
                res = requests.post(api_url, json=rule, headers=headers, verify=False, timeout=15)
                
                # Əgər hələ də 404 verərsə, alternativ yolu yoxla (bəzi QRadar AWS buildləri üçün)
                if res.status_code == 404:
                    api_url = f"{clean_url}/api/config/event_rules"
                    res = requests.post(api_url, json=rule, headers=headers, verify=False, timeout=15)
                
                print(f"QRadar: {rule['name']} - Status: {res.status_code}")
                
            except Exception as e:
                print(f"QRadar Xətası ({filename}): {e}")

if __name__ == "__main__":
    sync_splunk()
    sync_qradar()

