import os
import json
import requests
import urllib3

# SSL xəbərdarlıqlarını söndürürük
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GitHub Secrets-dən və ya Environment-dən məlumatları alırıq
SPLUNK_URL = os.getenv('SPLUNK_URL', '').strip()
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()

def sync_splunk():
    print("\n--- Splunk Sinxronizasiyası Başladı ---")
    path = "splunk/"
    
    if not os.path.exists(path):
        print(f"XƏTA: '{path}' qovluğu tapılmadı!")
        return
    
    files = [f for f in os.listdir(path) if f.endswith('.json')]
    print(f"Tapılan Splunk faylları: {len(files)}")

    # Sənin köhnə kodundakı Authorization formatı
    headers = {"Authorization": f"Splunk {SPLUNK_TOKEN}"}

    for filename in files:
        print(f"İşlənir: {filename}...")
        try:
            with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                rule = json.load(f)
                
                # Sənin xüsusi payload strukturun
                payload = {
                    "name": rule['name'],
                    "search": rule['search'],
                    "is_scheduled": 1,
                    "cron_schedule": rule.get('cron_schedule', '*/15 * * * *'),
                    "output_mode": "json"
                }
                
                api_url = f"{SPLUNK_URL}/services/saved/searches"
                
                # Köhnə kodundakı POST sorğusu
                res = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=10)
                
                if res.status_code in [201, 200]:
                    print(f"UĞURLU: {filename} (Status: {res.status_code})")
                else:
                    print(f"XƏTA: {filename} (Status: {res.status_code}) - {res.text}")
                    
        except Exception as e:
            print(f"Fayl oxunarkən xəta ({filename}): {e}")

if __name__ == "__main__":
    if not SPLUNK_URL or not SPLUNK_TOKEN:
        print("XƏTA: SPLUNK_URL və ya SPLUNK_TOKEN boşdur!")
    else:
        sync_splunk()


