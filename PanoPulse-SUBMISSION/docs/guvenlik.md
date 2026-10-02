# Təhlükəsizlik yanaşması

## Prinsip: şəbəkə seqmentasiyası birinci, API açarı ikinci

PanoPulse **heç vaxt internetə açıq olmamalıdır**. Nəzərdə tutulan yerləşdirmə:

```
İnternet  ──✗── (giriş yoxdur)
                    │
             IT şəbəkəsi (ofis)
                    │  firewall
             OT VLAN (SCADA, PanoPulse, RTU-lar)
                    │
             Sahə cihazları (TVOC-2, MPR-53CS, LoRa gateway-lər)
```

Bu, ADM/GDZ kimi paylayıcı şirkətlərin artıq öz SCADA infrastrukturunda
tətbiq etdiyi standart OT/IT ayrılığıdır — PanoPulse buna əlavə bir istisna
yaratmır, mövcud modelə uyğunlaşır.

## Tətbiq səviyyəsində qatlar (bu kod bazasında mövcud olan)

1. **API açarı** (`backend/app/auth.py`) — state-dəyişən endpoint-lər
   (ssenari tetikləmə, alert təsdiqi) `X-API-Key` header tələb edir.
   Oxuma endpoint-ləri (dashboard üçün) açıqdır, çünki əsas sərhəd artıq
   şəbəkə səviyyəsindədir.
2. **CORS** hazırda `*` olaraq qoyulub (development üçün) — istehsalda
   `allow_origins`-i yalnız on-prem dashboard-un öz domeninə
   məhdudlaşdırmaq lazımdır (`backend/app/main.py`-da bir sətir dəyişikliyi).
3. **Modbus TCP (5020/502)** — Modbus protokolunun özündə autentifikasiya
   yoxdur (bu, bütün sənaye Modbus tətbiqləri üçün doğrudur, MPR-53CS də
   daxil olmaqla) — buna görə bu port MÜTLƏQ OT VLAN daxilində qalmalı,
   heç bir halda IT şəbəkəsinə və ya internetə açılmamalıdır.

## Nə hələ edilməyib (dürüst etiraf)

- **İstifadəçi-səviyyəli autentifikasiya yoxdur** (kim, nə vaxt, hansı
  əməliyyatı etdi sualının tam cavabı). İstehsala keçiddə bu, ADM/GDZ-nin
  öz Active Directory/LDAP sisteminə inteqrasiya ilə həll olunmalıdır —
  bu, hazırkı hackathon mərhələsinin əhatəsindən kənardadır, amma
  yol xəritəsində açıq şəkildə qeyd olunur.
- **TLS/HTTPS yoxdur** — daxili OT VLAN-da, tam təcrid olunmuş şəbəkədə bu
  bəzən qəbul edilə bilər, amma tövsiyə edilən sonrakı addım daxili
  sertifikatla (internal CA) TLS-i aktivləşdirməkdir.
- **Rate limiting yoxdur** — kiçik, tam yerli bir sistem üçün hazırda
  prioritet deyil, amma böyümə ilə əlavə edilə bilər.

Bu siyahını gizlətmirik — texniki mentor/jüri sualı versə, konkret,
prioritetləşdirilmiş cavabımız var, "düşünməmişik" demirik.
