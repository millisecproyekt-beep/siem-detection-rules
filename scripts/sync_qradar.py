import os
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Səndə olan secret adlarına uyğunlaşdırırıq
# GitHub Secrets-də 'QRADAR_URL' olduğu üçün onu çağırırıq
QRADAR_BASE = os.getenv('QRADAR_URL', '').strip()
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

# Əgər QRADAR_URL içində yalnız IP (məs: 1.2.3.4) varsa, başına https:// əlavə edirik
if QRADAR_BASE and not QRADAR_BASE.startswith('http'):
    QRADAR_BASE = f"https://{QRADAR_BASE}"

headers = {
    'SEC': QRADAR_TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def get_rule_id_by_name(rule_name):
    # İndi URL tam və düzgün qurulacaq
    url = f"{QRADAR_BASE}/api/analytics/rules?filter=name%3D%22{rule_name}%22"
    res = requests.get(url, headers=headers, verify=False)
    if res.status_code == 200:
        data = res.json()
        return data[0]['id'] if data else None
    return None

# ... qalan funksiyalar (sync_qradar və s.)
