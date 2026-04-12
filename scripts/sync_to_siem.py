import os
import json
import requests
import urllib3
import zipfile  # QRadar extension paketi yaratmaq üçün əlavə edildi

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_URL = os.getenv('SPLUNK_URL', '').strip()
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()
QRADAR_URL = os.getenv('QRADAR_URL', '').strip()
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

# QRadar üçün sabitlər
QRADAR_RULES_DIR = "qradar"
ZIP_FILE_NAME = "qradar_rules_update.zip"

def sync_splunk():
    print("\n--- Splunk Yoxlanılır ---")
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

# --- QRADAR FUNKSİYALARI ---

def create_qradar_manifest():
    """QRadar-ın paketi qəbul etməsi üçün məcburi manifest faylı yaradır"""
    manifest_path = os.path.join(QRADAR_RULES_DIR, "manifest.txt")
    with open(manifest_path, "w") as f:
        f.write("Name=GitHub_SIEM_Rules\n")
        f.write("Version=1.0\n")
        f.write("Description=DCSync, Kerberoasting ve diger rule update-leri\n")
        f.write("Author=SOC Engineer\n")
    return manifest_path

def create_extension_zip():
    """qradar qovluğundakı faylları ZIP formatına salır"""
    create_qradar_manifest()
    with zipfile.ZipFile(ZIP_FILE_NAME, 'w') as zipf:
        for root, dirs, files in os.walk(QRADAR_RULES_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file)
    print(f"[+] QRadar Paketi yaradıldı: {ZIP_FILE_NAME}")

def sync_qradar():
    print("\n--- QRadar Yoxlanılır ---")
    if not os.path.exists(QRADAR_RULES_DIR):
        print(f"XƏTA: '{QRADAR_RULES_DIR}' qovluğu tapılmadı!")
        return

    if not QRADAR_URL or not QRADAR_TOKEN:
        print("[-] XƏTA: QRADAR_URL və ya QRADAR_TOKEN tapılmadı!")
        return

    # QRadar API URL-ni formalaşdırırıq
    extension_url = f"{QRADAR_URL.rstrip('/')}/api/config/extension_management/extensions"
    
    create_extension_zip()

    headers = {
        'SEC': QRADAR_TOKEN,
        'Accept': 'application/json'
    }

    print("[*] Paket QRadar-a yüklənir...")
    try:
        # 1. POST ilə zip faylını göndəririk
        with open(ZIP_FILE_NAME, 'rb') as f:
            files = {'file': (ZIP_FILE_NAME, f, 'application/zip')}
            upload_resp = requests.post(extension_url, headers=headers, files=files, verify=False, timeout=30)

        if upload_resp.status_code not in [201, 200]:
            print(f"[-] Yükləmə xətası: {upload_resp.text}")
            return

        extension_id = upload_resp.json().get('id')
        print(f"[+] Paket QRadar-a düşdü. Extension ID: {extension_id}")

        # 2. Paketi Install edirik
        print("[*] Qaydalar QRadar-a quraşdırılır (Install)...")
        install_url = f"{extension_url}/{extension_id}/install"
        install_resp = requests.post(install_url, headers=headers, verify=False, timeout=30)

        if install_resp.status_code in [200, 202]:
            print("[+] ƏLA! QRadar rule-ları uğurla yeniləndi.")
        else:
            print(f"[-] Quraşdırma xətası: {install_resp.text}")
            
    except Exception as e:
        print(f"QRadar sinxronizasiyası zamanı xəta: {e}")

if __name__ == "__main__":
    # GitHub Actions işə düşəndə hər iki SİEM avtomatik yenilənəcək
    sync_splunk()
    sync_qradar()
