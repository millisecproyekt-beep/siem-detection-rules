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
    print("\n--- 🛡️ QRadar REAL Rule Deployment Başladı ---")
    
    # URL-i təmizləyirik (sonundakı / və /api hissələrini yoxlayırıq)
    base_url = os.getenv('QRADAR_URL', '').strip().rstrip('/')
    if base_url.endswith('/api'):
        base_url = base_url[:-4]
    
    token = os.getenv('QRADAR_TOKEN', '').strip()
    
    # KRİTİK: Endpoint və Headers
    api_url = f"{base_url}/api/analytics/rules"
    headers = {
        "SEC": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "19.0"  # Versiyanı bura əlavə etdik ki, POST metodu aktivləşsin
    }

    path = "qradar/"
    if not os.path.exists(path):
        print(f"❌ '{path}' qovluğu tapılmadı!")
        return

    for filename in sorted(os.listdir(path)):
        if filename.endswith('.json'):
            print(f"🔄 Göndərilir: {filename}...")
            with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                try:
                    rule_data = json.load(f)
                    res = requests.post(api_url, json=rule_data, headers=headers, verify=False, timeout=30)
                    
                    if res.status_code in [200, 201]:
                        print(f"✅ UĞURLU: {rule_data.get('name')}")
                    elif res.status_code == 409:
                        print(f"ℹ️ MÖVCUDDUR: {rule_data.get('name')} artıq var.")
                    else:
                        print(f"❌ XƏTA ({filename}): {res.status_code}")
                        print(f"Mesaj: {res.text}")
                except Exception as e:
                    print(f"⚠️ Problem: {e}")

    # DEPLOY CHANGES
    print("\n🔄 QRadar-da Dəyişikliklər tətbiq edilir...")
    requests.post(f"{base_url}/api/system/staging/deploy", headers=headers, verify=False)
            
if __name__ == "__main__":
    sync_splunk()
    sync_qradar()
