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
    QRADAR_URL = os.getenv('QRADAR_URL', '').strip().rstrip('/')
    QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

    print(f"\n--- QRadar REAL Rule Deployment Başladı ---")
    path = "qradar/"
    headers = {
        "SEC": QRADAR_TOKEN, 
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # 1. Qaydanı Yaratmaq/Yeniləmək üçün API endpoint
    rules_api = f"{QRADAR_URL}/api/analytics/rules"

    for filename in [f for f in os.listdir(path) if f.endswith('.json')]:
        with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
            try:
                rule_payload = json.load(f) # JSON artıq tam QRadar Rule formatında olmalıdır
                
                # QRadar-a POST sorğusu
                res = requests.post(rules_api, json=rule_payload, headers=headers, verify=False, timeout=30)
                
                if res.status_code in [201, 200]:
                    print(f"✅ QRadar Qaydası Yaradıldı: {rule_payload.get('name')}")
                elif res.status_code == 409:
                    print(f"ℹ️ {rule_payload.get('name')} artıq var, yeniləmə tələb olunur (PUT).")
                else:
                    print(f"❌ Xəta: {filename} -> {res.status_code}: {res.text}")

            except Exception as e:
                print(f"⚠️ {filename} faylında problem: {e}")

    # 2. KRİTİK: Qaydanın aktivləşməsi üçün Deploy Changes (Pramoy işləməsi üçün)
    print("🔄 Dəyişikliklər tətbiq edilir (Deploying Changes)...")
    deploy_url = f"{QRADAR_URL}/api/system/staging/deploy"
    requests.post(deploy_url, headers=headers, verify=False)
            
if __name__ == "__main__":
    sync_splunk()
    sync_qradar()
