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
    print(f"\n--- QRadar Sinxronizasiyası Başladı ---")
    path = "qradar/"
    if not os.path.exists(path): return
    
    headers = {
        "SEC": QRADAR_TOKEN, 
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "27.0"
    }
    
    for filename in [f for f in os.listdir(path) if f.endswith('.json')]:
        with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
            rule_data = json.load(f)
            # QRadar-da AQL axtarışlarını yadda saxlamaq üçün ən doğru yol:
            api_url = f"{QRADAR_URL.rstrip('/')}/api/siem/offense_saved_searches"
            
            try:
                res = requests.post(api_url, json=rule_data, headers=headers, verify=False, timeout=15)
                
                if res.status_code in [201, 200]:
                    print(f"✅ QRadar: {rule_data['name']} uğurla yaradıldı! (Status: {res.status_code})")
                elif res.status_code == 409:
                    print(f"ℹ️ QRadar: {rule_data['name']} artıq mövcuddur. (Status: 409)")
                else:
                    print(f"❌ QRadar Xətası: {filename} -> Status: {res.status_code}")
                    print(f"Cavab: {res.text}") # Xətanın səbəbini görmək üçün
            except Exception as e:
                print(f"⚠️ Bağlantı xətası ({filename}): {e}")
            
if __name__ == "__main__":
    sync_splunk()
    sync_qradar()

