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
    print("\n--- 🛡️ QRadar Rule Deployment Başladı ---")
    
    QRADAR_URL = os.getenv('QRADAR_URL', '').strip().rstrip('/')
    QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()
    
    if not QRADAR_URL or not QRADAR_TOKEN:
        print("❌ QRadar URL və ya Token tapılmadı!")
        return

    path = "qradar/"
    headers = {
        "SEC": QRADAR_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # QRadar Qaydaları üçün REAL endpoint
    api_url = f"{QRADAR_URL}/api/analytics/rules"

    if not os.path.exists(path):
        print(f"❌ '{path}' qovluğu tapılmadı!")
        return

    for filename in [f for f in os.listdir(path) if f.endswith('.json')]:
        print(f"🔄 İşlənir: {filename}...")
        with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
            try:
                rule_data = json.load(f)
                
                # Qaydanı QRadar-a göndəririk
                res = requests.post(api_url, json=rule_data, headers=headers, verify=False, timeout=30)
                
                if res.status_code in [200, 201]:
                    print(f"✅ UĞURLU: {rule_data.get('name')} yaradıldı.")
                elif res.status_code == 409:
                    print(f"ℹ️ MÖVCUDDUR: {rule_data.get('name')} artıq sistemdə var.")
                else:
                    print(f"❌ XƏTA: {filename} -> Status: {res.status_code}")
                    print(f"Detallı xəta mesajı: {res.text}")
                    
            except Exception as e:
                print(f"⚠️ {filename} faylı oxunarkən xəta: {e}")

    # DEPLOY CHANGES (Bütün qaydalardan sonra bircə dəfə)
    print("\n🔄 QRadar-da dəyişikliklər tətbiq edilir (Deploying Changes)...")
    deploy_res = requests.post(f"{QRADAR_URL}/api/system/staging/deploy", headers=headers, verify=False)
    if deploy_res.status_code in [200, 201, 202]:
        print("🚀 Deploy uğurla başladıldı!")
    else:
        print(f"⚠️ Deploy xətası: {deploy_res.text}")
            
if __name__ == "__main__":
    sync_splunk()
    sync_qradar()
