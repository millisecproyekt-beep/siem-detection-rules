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
    print(f"\n--- QRadar Tam Diaqnostika Başladı ---")
    path = "qradar/"
    if not os.path.exists(path): return
    
    # QRadar-da bu versiyada POST adətən bu ünvanlarda olur
    endpoints = ["/api/analytics/rules", "/api/config/event_rules"]
    # Versiyaları aşağıdan yuxarı yoxlayaq
    versions = ["12.0", "15.0", "19.0", "27.0"]

    for filename in [f for f in os.listdir(path) if f.endswith('.json')]:
        with open(os.path.join(path, filename), 'r') as f:
            rule_data = json.load(f)
            
            for ep in endpoints:
                for ver in versions:
                    headers = {"SEC": QRADAR_TOKEN, "Content-Type": "application/json", "Version": ver}
                    url = f"{QRADAR_URL.rstrip('/')}{ep}"
                    try:
                        res = requests.post(url, json=rule_data, headers=headers, verify=False, timeout=5)
                        if res.status_code in [200, 201]:
                            print(f"✅ TAPILDI! Yol: {ep}, Versiya: {ver}, Status: {res.status_code}")
                            return # Birini tapdıqsa kifayətdir
                    except: continue
    print("❌ Təəssüf ki, heç bir kombinasiya işləmədi.")
if __name__ == "__main__":
    sync_splunk()
    sync_qradar()

