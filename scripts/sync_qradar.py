import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GitHub Secrets-dən dəyərləri çəkirik
QRADAR_BASE = os.getenv('QRADAR_URL', '').strip()
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

if QRADAR_BASE and not QRADAR_BASE.startswith('http'):
    QRADAR_BASE = f"https://{QRADAR_BASE}"

headers = {
    'SEC': QRADAR_TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def get_all_rules():
    """QRadar-dakı mövcud qaydaları çəkir"""
    url = f"{QRADAR_BASE}/api/analytics/rules"
    res = requests.get(url, headers=headers, verify=False)
    return res.json() if res.status_code == 200 else []

def update_rule(rule_id, github_payload):
    """Mövcud qaydanı ID üzərindən POST ilə yeniləyir"""
    url = f"{QRADAR_BASE}/api/analytics/rules/{rule_id}"
    
    # QRadar API qaydalar üçün yalnız müəyyən sahələri yeniləməyə icazə verir (məs: enabled/disabled)
    clean_payload = {"enabled": github_payload.get("enabled", True)}
    
    res = requests.post(url, headers=headers, json=clean_payload, verify=False)
    return res.status_code

def sync():
    print(f"--- QRadar API Sinxronizasiyası: {QRADAR_BASE} ---")
    
    if not QRADAR_BASE or not QRADAR_TOKEN:
        print("XƏTA: QRADAR_URL və ya QRADAR_TOKEN secret-ləri boşdur! GitHub Settings-i yoxla.")
        return

    qradar_rules = get_all_rules()
    path = "qradar/"
    
    # Github-dakı bütün json fayllarını oxuyuruq
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename), 'r') as f:
                local_rule = json.load(f)
                rule_name = local_rule.get('name', '').strip()
                
                # QRadar-dakı qayda ilə adı müqayisə edirik
                match = next((r for r in qradar_rules if r.get('name', '').strip() == rule_name), None)
                
                if match:
                    r_id = match['id']
                    print(f"Yenilənir: '{rule_name}' (ID: {r_id})")
                    status = update_rule(r_id, local_rule)
                    if status in [200, 201, 202]:
                        print("  [OK] Qayda uğurla API vasitəsilə yeniləndi!")
                    else:
                        print(f"  [XƏTA] Status: {status}")
                else:
                    # QRadar API sıfırdan yaratmağa icazə vermədiyi üçün Placeholder məntiqi işləyir

                    
