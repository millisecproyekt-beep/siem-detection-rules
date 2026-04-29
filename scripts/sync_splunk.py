import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GitHub Secret-dən gələn URL (Məsələn: https://45.55.59.89)
SPLUNK_BASE = os.getenv('SPLUNK_URL', '').strip().rstrip('/')
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()

def sync_splunk():
    print(f"\n--- Splunk Sinxronizasiyası Başladı: {SPLUNK_BASE} ---")
    
    # 8000 portunu 8089 ilə əvəz edirik və ya yoxdursa əlavə edirik
    if ":8000" in SPLUNK_BASE:
        api_base = SPLUNK_BASE.replace(":8000", ":8089")
    elif ":8089" not in SPLUNK_BASE:
        api_base = f"{SPLUNK_BASE}:8089"
    else:
        api_base = SPLUNK_BASE

    path = "splunk/"
    if not os.path.exists(path):
        print(f"XƏTA: '{path}' qovluğu tapılmadı!")
        return

    # JWT Token üçün başlıqlar
    headers = {
        "Authorization": f"Bearer {SPLUNK_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    files = [f for f in os.listdir(path) if f.endswith('.json')]
    
    for filename in files:
        try:
            with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                rule = json.load(f)
                
                # API Endpoint
                api_url = f"{api_base}/services/saved/searches?output_mode=json"
                
                payload = {
                    "name": rule['name'],
                    "search": rule['search'],
                    "is_scheduled": 1,
                    "cron_schedule": rule.get('cron_schedule', '*/15 * * * *'),
                    "disabled": 0
                }
                
                print(f"Göndərilir: {rule['name']} -> {api_url}")
                res = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=15)
                
                if res.status_code in [200, 201]:
                    print(f"✅ UĞURLU: {filename}")
                else:
                    print(f"❌ XƏTA: {filename} (Status: {res.status_code}) - {res.text[:100]}")
                    
        except Exception as e:
            print(f"❌ XƏTA: {str(e)}")

if __name__ == "__main__":
    sync_splunk()
