"""
PanoPulse — minimal auth qatı
--------------------------------
Zəiflik: ilk versiyada heç bir auth yox idi — istənilən şəbəkə üzvü
ssenari tetikləyə və ya alertləri təsdiqləyə bilərdi.

Bu, tam kimlik idarəetmə sistemi DEYİL (o, ADM/GDZ-nin öz AD/LDAP-ına
inteqrasiya tələb edər — istehsala keçiddə növbəti addım kimi
sənədləşdirilib). Bu, hazırkı mərhələ üçün MƏNTİQLİ bir müdafiə
qatıdır: state-dəyişən (yazma) endpoint-lər statik API açarı tələb
edir; oxuma endpoint-ləri (dashboard-un ehtiyac duyduğu) açıq qalır,
çünki əsas müdafiə xətti artıq şəbəkə səviyyəsindədir (bax aşağı).

Əsas müdafiə: bu server HEÇ VAXT internetə açıq DEYİL — yalnız
ADM/GDZ-nin OT (Operational Technology) VLAN-ında, IT şəbəkəsindən
firewall ilə ayrılmış şəkildə işləməlidir. API açarı ikinci qatdır,
birinci deyil.
"""
import os
import secrets
from fastapi import Header, HTTPException

# Prod-da mühit dəyişəni ilə verilir; demo üçün default dəyər.
API_KEY = os.environ.get("PANOPULSE_API_KEY", "panopulse-dev-key-CHANGE-ME")


def require_api_key(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Geçersiz veya eksik X-API-Key")
    return True
