import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RAW_INPUT = os.getenv('SPLUNK_URL', '').strip()
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()

# IP-ni təmizləyirik
clean_host = RAW_INPUT.replace("https://", "").replace("http://", "").split('/')[0].split(':')[0]
API_BASE = f"https://{clean_host}:8089"

def sync_splunk():
    print(f"--- Splunk API Ünvanı: {API_BASE} ---")
    
    headers = {
        "Authorization": f"Bearer {SPLUNK_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    path = "splunk/"
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                    rule = json.load(f)
                    
                    api_url = f"{API_BASE}/services/saved/searches?output_mode=json"
                    
                    # BURADA CRON_SCHEDULE ƏLAVƏ EDİLDİ
                    payload = {
                        "name": rule['name'],
                        "search": rule['search'],
                        "is_scheduled": 1,
                        "cron_schedule": rule.get('cron_schedule', '*/15 * * * *'), # JSON-da yoxdursa 15 dəqiqə
                        "disabled": 0
                    }
                    
                    res = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=15)
                    
                    if res.status_code in [200, 201]:
                        print(f"✅ UĞURLU: {filename}")
                    else:
                        print(f"❌ XƏTA: {filename} (Status: {res.status_code}) - {res.text[:100]}")
            except Exception as e:
                print(f"❌ XƏTA ({filename}): {str(e)}")

if __name__ == "__main__":
    sync_splunk()
