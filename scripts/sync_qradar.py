"""
sync_qradar.py
GitHub → QRadar sinxronizasiya skripti

QRadar REST API məhdudiyyəti:
  - POST /api/analytics/rules        → MÖVCUD DEYİL (create yoxdur!)
  - POST /api/analytics/rules/{id}   → UPDATE edir (bu işləyir)
  - GET  /api/analytics/rules        → Hamısını çəkir

Strategiya:
  1. QRadar-dan bütün mövcud rule-ları çək
  2. GitHub-dakı hər JSON faylı üçün ada görə match tap
  3. Match varsa → POST /api/analytics/rules/{id} ilə update et
  4. Match yoxdursa → Warning ver (manual UI-da yaratmaq lazımdır)
"""

import os
import sys
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── Config ───────────────────────────────────────────────────────────────────

QRADAR_BASE  = os.getenv("QRADAR_URL", "").strip()
QRADAR_TOKEN = os.getenv("QRADAR_TOKEN", "").strip()

if QRADAR_BASE and not QRADAR_BASE.startswith("http"):
    QRADAR_BASE = f"https://{QRADAR_BASE}"

HEADERS = {
    "SEC": QRADAR_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Version": "12.0"     # QRadar API versiyası – öz versiyanda dəyişdir
}

RULES_DIR = os.path.join(os.path.dirname(__file__))  # qradar/ qovluğu

# QRadar POST-da qəbul etmədiyi read-only sahələr
FORBIDDEN_FIELDS = {
    "id", "identifier", "owner", "creation_date",
    "modification_date", "origin", "base_host_id_set"
}

# ─── API Funksiyaları ─────────────────────────────────────────────────────────

def get_all_qradar_rules() -> list:
    """QRadar-dakı bütün mövcud rule-ları çəkir."""
    url = f"{QRADAR_BASE}/api/analytics/rules"
    try:
        res = requests.get(url, headers=HEADERS, verify=False, timeout=30)
        res.raise_for_status()
        rules = res.json()
        print(f"[INFO] QRadar-dan {len(rules)} rule çəkildi.")
        return rules
    except requests.exceptions.ConnectionError:
        print(f"[XƏTA] QRadar-a qoşulmaq mümkün olmadı: {QRADAR_BASE}")
        print("       IP/URL-i, VPN-i və ya firewall-u yoxla.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"[XƏTA] HTTP Error: {e.response.status_code} - {e.response.text}")
        sys.exit(1)

def get_rule_detail(rule_id: int) -> dict:
    """Bir rule-un tam detallarını çəkir (POST üçün tam payload lazımdır)."""
    url = f"{QRADAR_BASE}/api/analytics/rules/{rule_id}"
    res = requests.get(url, headers=HEADERS, verify=False, timeout=30)
    if res.status_code == 200:
        return res.json()
    print(f"[XƏTA] Rule detail alınamadı (ID:{rule_id}): {res.status_code}")
    return {}

def update_rule(rule_id: int, github_payload: dict, rule_name: str) -> bool:
    """
    Mövcud rule-u POST ilə yeniləyir.
    QRadar POST /api/analytics/rules/{id} – update endpoint.
    
    Öncə mövcud rule-un tam detalını çəkib üzərinə GitHub payloadunu merge edirik.
    Bu olmadan 'missing required field' xətası gəlir.
    """
    # 1. Mövcud rule-un tam state-ini çək
    existing = get_rule_detail(rule_id)
    if not existing:
        return False

    # 2. Mövcud state üzərinə GitHub-dan gələn dəyişiklikləri tət et
    merged = {**existing, **github_payload}

    # 3. Forbidden (read-only) sahələri sil
    clean_payload = {k: v for k, v in merged.items() if k not in FORBIDDEN_FIELDS}

    # 4. POST et
    url = f"{QRADAR_BASE}/api/analytics/rules/{rule_id}"
    try:
        res = requests.post(
            url,
            headers=HEADERS,
            json=clean_payload,
            verify=False,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        print(f"  [XƏTA] Request failed: {e}")
        return False

    if res.status_code in (200, 201, 202):
        print(f"  [OK] '{rule_name}' uğurla yeniləndi (HTTP {res.status_code})")
        return True
    else:
        print(f"  [XƏTA] '{rule_name}' yenilənəmdi → HTTP {res.status_code}")
        try:
            err_body = res.json()
            print(f"         QRadar cavabı: {json.dumps(err_body, indent=2)}")
        except Exception:
            print(f"         Raw cavab: {res.text[:300]}")
        return False

# ─── Ana Sinxronizasiya ───────────────────────────────────────────────────────

def sync():
    print("=" * 60)
    print(f"  QRadar Sinxronizasiyası")
    print(f"  Target: {QRADAR_BASE}")
    print("=" * 60)

    # Secret yoxlaması
    if not QRADAR_BASE or not QRADAR_TOKEN:
        print("[XƏTA] QRADAR_URL və ya QRADAR_TOKEN boşdur!")
        print("       GitHub Settings → Secrets-i yoxla.")
        sys.exit(1)

    # QRadar-dan mövcud rule-ları çək
    qradar_rules = get_all_qradar_rules()

    # Ada görə axtarma üçün dict (lowercase normalisation)
    rules_by_name = {r["name"].strip().lower(): r for r in qradar_rules}

    # GitHub-dakı JSON fayllarını oxu
    json_files = [f for f in os.listdir(RULES_DIR) if f.endswith(".json")]

    if not json_files:
        print(f"[WARNING] '{RULES_DIR}' qovluğunda heç bir .json tapılmadı.")
        return

    print(f"\n[INFO] {len(json_files)} JSON faylı tapıldı. İşlənir...\n")

    updated  = []
    skipped  = []
    failed   = []

    for filename in sorted(json_files):
        filepath = os.path.join(RULES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                local_rule = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[XƏTA] JSON parse error ({filename}): {e}")
            failed.append(filename)
            continue

        rule_name = local_rule.get("name", "").strip()
        if not rule_name:
            print(f"[XƏTA] '{filename}' faylında 'name' sahəsi yoxdur.")
            failed.append(filename)
            continue

        print(f"→ İşlənir: '{rule_name}' ({filename})")

        match = rules_by_name.get(rule_name.lower())

        if match:
            rule_id = match["id"]
            print(f"  Tapıldı → QRadar ID: {rule_id}")
            success = update_rule(rule_id, local_rule, rule_name)
            (updated if success else failed).append(rule_name)
        else:
            # QRadar API-də CREATE yoxdur – manual yaratmaq lazımdır
            print(f"  [!] '{rule_name}' QRadar-da tapılmadı.")
            print(f"      → QRadar UI-da bu adla manual yarat, sonra bu script update edəcək.")
            skipped.append(rule_name)

    # ─── Yekun Hesabat ───
    print("\n" + "=" * 60)
    print(f"  YEKUN:")
    print(f"  Uğurla yeniləndi : {len(updated)}")
    print(f"  Tapılmadı (skip) : {len(skipped)}")
    print(f"  Xəta             : {len(failed)}")
    print("=" * 60)

    if skipped:
        print("\n[!] QRadar UI-da əl ilə yaradılmalı olan rule-lar:")
        for name in skipped:
            print(f"    - {name}")

    if failed:
        print("\n[XƏTA] Uğursuz fayllar:")
        for name in failed:
            print(f"    - {name}")
        sys.exit(1)   # CI/CD-ni fail et ki, Actions-da görünsün

if __name__ == "__main__":
    sync()
