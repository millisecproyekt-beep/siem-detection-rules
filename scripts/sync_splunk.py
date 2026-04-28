import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_URL = os.getenv('SPLUNK_URL', '').strip()
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()

def sync_splunk():
    print("\n--- Splunk Sinxronizasiyası Başladı ---")
    path = "splunk/"
    
    if not os.path.exists(path):
        print(f"XƏTA: '{path}' qovluğu tapılmadı!")
        return
    
    files = [f for f in os.listdir(path) if f.endswith('.json')]
    
    # Sənin orijinal Authorization formatın
    headers = {"Authorization": f"Splunk {SPLUNK_TOKEN}"}

    for filename in files:
        try:
            with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                rule = json.load(f)
                
                # Sənin Splunk üçün hazırladığın xüsusi payload
                payload = {
                    "name": rule['name'],
                    "search": rule['search'],
                    "is_scheduled": 1,
                    "cron_schedule": rule.get('cron_schedule', '*/15 * * * *'),
                    "output_mode": "json"
                }
                
                api_url = f"{SPLUNK_URL}/services/saved/searches"
                res = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=10)
                
                print(f"İşlənir: {filename} -> Status: {res.status_code}")
        except Exception as e:
            print(f"Xəta ({filename}): {e}")

if __name__ == "__main__":
    sync_splunk()
