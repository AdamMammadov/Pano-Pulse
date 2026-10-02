# PanoPulse

**Pano/hücre içi anomali erken uyarı sistemi** — Grid Up Hackathon (ADM & GDZ Elektrik) için geliştirilmektedir.

Takım #126 (Turquoise Hamster) — Adam Mammadov, Lala Shirinli

## Durum (20 Eylül 2026 itibariyle — final teslim)

✅ Tamamlanan:
- Sentetik sensör simülasyonu (Akım, ARC, PD, Ortam) — organizatörün paylaştığı gerçek cihaz
  spesifikasyonlarıyla (ABB TVOC-2, Techimp HFCT, MPR-53CS) birebir uyumlu format
- Anomali tespit + çok-sensörlü risk füzyon motoru (z-score + persistence filter,
  GridPulse'un v1→v5 kalibrasyon derslerinden uyarlandı)
- **Ampirik kalibre edilmiş**: yanlış alarm oranı 1.87 → 0.024/pano/gün (78x iyileşme),
  gerçek tespit hızı ~1 dakika gecikmeyle (bkz. docs/kalibrasyon.md)
- 120 panoluk (>=100 gereksinimini karşılayan) canlı simülasyon + FastAPI backend
- **SQLite ile kalıcılık** — geçmiş ve alarm kayıtları restart'ta kaybolmaz (storage.py)
- **API-key korumalı** yazma uç noktaları + dokümante edilmiş ağ segmentasyonu stratejisi
  (bkz. docs/guvenlik.md)
- **20 otomatik test** (pytest) — anomali mantığı + health score + forensics + what-if + API + PDF + Telegram degradasiyonu, hepsi yeşil
- On-prem uyumlu mimari (public cloud bağımlılığı yok) + Docker/docker-compose ile
  tek komutla dağıtım (build bu ortamda doğrulanamadı, bkz. not aşağıda; docker-compose.yml
  sözdizimi doğrulandı)
- SMS/WhatsApp alarm mekanizması (local gateway arayüzü olarak, mock + gerçek entegrasyon noktası hazır)
- **Telegram bildiriş inteqrasiyası** — kod tam yazılıb, tokensiz vəziyyətdə "sakit
  degradasiya" test edilib
- React dashboard, tamamen İngilizce arayüz, 4 ana görünüm + canlı demo modu:
  - **Cabinet Detail** — sensör kartları, risk göstergesi (Gauge), risk geçmişi grafiği,
    kök-səbəb faizli dağılımı, kestirimci baxım proqnozu
  - **Digital Twin** — pano kesitinin canlı, renk-kodlu şematik görselleştirilmesi
    (ARC, L1/L2/L3, Gateway, Nem/PD zonaları), 150A+ yük eşiğinde çerçeve rəngi dəyişimi
  - **Fleet Overview** — 120 panonun risk paylanmasının zaman-seriyalı trendi, Sistem
    Sağlığı göstəricisi, Top-5 riskli pano cədvəli, filo-geneli maliyyət təxmini,
    tək düymə ilə çoxlu-pano simulyasiyası
  - **AI Co-Pilot** — ayrıca, böyüdülmüş həsr olunmuş görünüş, typewriter animasiyası
  - **Presentation Mode** (▶) — 40 saniyəlik tam avtomatik demo ssenarisi: normal→anomaliya→
    real aşkarlanma gözləyən AI şərhi→iş əmri→bərpa, real vaxtla sinxron
  - İzgara/liste keçidi, axtarış, filtr ("yalnız uyarısı olanlar"), hover tooltip
    (yük/risk), klikləyəndə birbaşa detala keçid
- **Gerçek, çalışan Modbus TCP server** (port 5020) — her panonun füzyon sonucunu
  20 registerlik bir blokta SCADA'ya sunar. `test_modbus_client.py` ile bağımsız bir
  Modbus istemcisiyle doğrulandı
- Fiziksel modül konsepti + PCB blok şeması + kablosuz sensör seçimi (bkz. docs/)
- Maliyet/fayda analizi (docs/maliyet_fayda.md) + **canlı, redaktə edilə bilən Maliyyət
  Etki kalkulyatoru** (real proqnoz saatına bağlı) və **ESG/Enerji itki kalkulyatoru**
  (P=I²R fizika düsturu ilə, uydurma rəqəm yoxdur — hər ikisi şəffaf fərziyyələrlə)
- **Kestirimci bakım (predictive maintenance)** — yüzey sıcaklığı trendine xətti
  reqressiya uyğunlaşdırılır, canlı geri-sayım taymeri (HH:MM:SS) ilə göstərilir
- **Kök səbəb faizli sıralaması** — z-score-lara əsaslanan, sıralı ehtimal dağılımı
  (məs. "Gevşek klemens — %52, Aşırı yüklenme — %48")
- **AI Co-Pilot** proqnoz və kök-səbəbi cavablara inteqrasiya edir, geniş sual dəstəyi
  (salamlaşma, sistem icmalı, akım/temperatur/nəm/PD sualları) — konkret, amma
  uydurma texniki ədəd (tork, amper həddi və s.) VERMİR, bu bilərəkdən edilib
  (yanlış bir ədəd real sahə zədəsinə səbəb ola bilər). Cavabın altında PDF hesabat
  və (demo) iş əmri düymələri
- **Avtonom Müdafiə simulyasiyası** — risk 90+ olanda popup, "Auto-Trip Load Shedding"
  düyməsi ilə — açıq "SİMÜLASYONDUR" xəbərdarlığı ilə (real relə/şalter əməliyyatı yoxdur)
- **Demo effektləri** — kritik vəziyyətdə vizual yanıb-sönmə + sintetik alarm səsi +
  yeni alertlərdə çatdırma-kanalı təsdiqi olan bildiriş toast-ı
- **PDF hadisə hesabatı** (`GET /cabinets/{id}/report.pdf`) — DejaVu Unicode fontu
  bundle edilib (türk/azərbaycan hərfləri düzgün göstərilir), TEDAŞ-MLZ/ABB TVOC-2
  standart istinadları ilə
- **AR konsept önizləməsi** — gələcək inkişaf fikri, aydın "işlək deyil, mockup"
  etiketi ilə (real AR/WebXR inteqrasiyası hazırkı əhatədə deyil)
- **What-If Simulator** — "nəm 20% artsa risk necə olar?" tərzi sual-cavab; real
  aşkarlama mühərrikinin ÜZƏRİNDƏ, heç bir real state-i dəyişmədən (read-only
  proqnozlaşdırma, avtomatik testlərlə qorunur)
- **Emergency Mode** — kritik pano seçiləndə tam ekran xəbərdarlıq, ACKNOWLEDGE
  / VIEW INCIDENT / CREATE WORK ORDER düymələri ilə
- **Risk Heatmap** — 120 panonun substation-tərzi, nömrələnmiş grid görünüşü
  (Fleet Overview-da)
- **Cabinet Health Score** — ani risk skorundan fərqli, uzunmüddətli etibarlılıq
  göstəricisi (təkrarlanan anomaliyalar zamanla düşürür, hətta cari tick
  normal görünsə belə) — komanda üzvü Lala Shirinli tərəfindən qurulub
- **Top Priority Panels** — sırf risk skoru yox, risk+persistence+proqnoz
  təcililiyinin çəkili düsturu ilə sıralanan prioritet siyahısı (Lala Shirinli)
- **Digital Forensics / Incident Timeline** — hər anomaliya anının tam sensor
  görüntüsü ilə saxlanması, "bu niyə baş verdi?" sualına dəlil-əsaslı cavab
  (backend: Lala Shirinli, frontend: tamamlanma turu)

⚠️ Dürüst sınırlamalar:
- Docker build bu sandbox ortamında test edilemedi (Docker/registry erişimi yok) —
  Dockerfile'lar standart, yaygın kalıpları izliyor, docker-compose.yml sözdizimi
  doğrulandı, ama gerçek makinede tam çalıştırma doğrulanmalı
- PD (kısmi deşarj) verisi sentetiktir — gerçek Techimp analizör çıktı formatı
  entegre edilmedi (bkz. docs/fiziki_modul_ve_sensor_secimi.md)
- Kullanıcı-seviyeli auth yok (API-key var, AD/LDAP entegrasyonu değil)
- **Denendi, geçici olarak geri alındı, sonra izole edilmiş şəkildə YENİDƏN qoşuldu,
  VƏ İNDİ TAM İŞLƏYİR** ✅: AG-001 üçün gerçek bir Modbus master/slave round-trip
  (`device_process.py` + `bridge_process.py`, gerçek MPR-53CS/TVOC-2 register
  adresleriyle). İlk entegrasyon denemesi ana uygulamayı asıyordu. Çözüm: bu
  bileşeni TAMAMEN AYRI İKİ ALT SÜREÇTE izole ettik. Takım üyesi Lala Shirinli
  bu izole modül üzerinde ayrıca çalışarak İKİ gerçek kök nedeni buldu ve
  düzeltti: (1) async pymodbus istemcisi bu ortamda kararsızdı → senkron
  pyModbusTCP'ye geçirildi (auto_open=True, timeout=2.0); (2) device_process.py'nin
  akım değerini register'a yazarken kullandığı ×1000 çarpanı, gerçekçi akım
  değerlerinde (örn. 300A → 300,000) uint16 sınırını (65,535) aşıyordu →
  kaldırıldı. Entegrasyon sırasında bridge'in okuma tarafında kalan bir ölçek
  uyuşmazlığı (hâlâ /1000 yapıyordu) ve `link_ok`'un gerçek başarı/başarısızlığa
  değil sabit `1`'e bağlı olması ayrıca düzeltildi. **Sonuç: AG-001 paneli artık
  gerçek bir Modbus TCP client-server round-trip üzerinden canlı veri gösteriyor**
  (dashboard'da "🔌 Live Modbus" rozeti), 45 saniyelik tekrarlı testte 8/8 başarı
  ile doğrulandı. Ana sistem yine de her koşulda %100 kararlı kalır (bridge
  çökse/asılsa bile ana API etkilenmez) — bu artık kazanılmış bir bonus, bir
  gereklilik değil.
- Bazı iç dokümantasyon (bu README, docs/) hâlâ Türkçe/Azerice karışık — arayüzün
  kendisi tamamen İngilizceye çevrildi, dokümantasyon temizliği son adımlardan biridir

🔜 Sırada:
- Dokümantasyon dil temizliği (README + docs/ → tutarlı tek dil)
- Gerçek RS-485/TVOC-2 donanımıyla saha testi (hackathon kapsamı dışında, gelecek adım)

## Mimari

```
Sensörler (CT / ARC / PD / Temp-Nem)
        ↓
Yerli gateway (Modbus master, mikrodenetleyici — ESP32-S3)
        ↓
On-prem monitorinq mühərriki (bu repo — anomaly_engine.py + storage.py)
        ↓
   ┌────┴────┬──────────┐
SCADA/Modbus  Dashboard  SMS/WhatsApp
(port 5020)   (React)    (yerli gateway)
```

## Çalıştırma

**Yerel (manuel):**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd frontend
npm install
npm run dev
```

**Docker (tek komut — doğrulanmamış, bkz. yukarı):**
```bash
docker compose up -d
```

Dashboard: http://localhost:5173 (veya Docker'da :80) · API: http://localhost:8000 · Modbus TCP: localhost:5020

**SCADA entegrasyonunu test etmek için** (backend çalışırken, ayrı bir terminalde):
```bash
cd backend
python test_modbus_client.py        # AG-001'i okur
python test_modbus_client.py 5      # AG-005'i okur
```

**AG-001 için gerçek Modbus round-trip'i (device_process + bridge_process)
backend'i başlattığınızda OTOMATİK olarak arka planda çalışır** — ayrıca bir
şey yapmanız gerekmiyor. Çalışıp çalışmadığını kontrol etmek için:
```bash
cd backend
python -c "import sqlite3; print(sqlite3.connect('panopulse.db').execute(\"SELECT * FROM field_gateway_state\").fetchone())"
# link_ok=1 ise çalışıyor demektir; /cabinets/AG-001 çıktısında data_source='modbus_live' görürsünüz.
# link_ok=0 ise (bu sandbox'ta olduğu gibi) sistem sessizce 'synthetic'e döner — çökmez.
```

**Testleri çalıştırmak için:**
```bash
cd backend
pytest tests/ -v
```

**Telegram bildirimini etkinleştirmek için** (opsiyonel — token olmadan sistem
sessizce devre dışı kalır, çökmez):
```bash
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
uvicorn app.main:app --port 8000
```

## Dokümantasyon

- `docs/fiziki_modul_ve_sensor_secimi.md` — gateway modülü, sensör seçimi ve gerekçesi
- `docs/kalibrasyon.md` — yanlış alarm oranı ölçüm metodolojisi ve sonuçları
- `docs/guvenlik.md` — güvenlik yaklaşımı ve dürüst sınırlamalar
- `docs/maliyet_fayda.md` — maliyet/fayda analizi
- `docs/demo_senaryosu.md` — demo videosu çekim rehberi
- `GET /modbus/register-map` — canlı register haritası (API üzerinden)
- `GET /docs` — FastAPI'nin otomatik ürettiği interaktif API dokümantasyonu

## AI aracı kullanım beyanı (Taahhütname Madde 4 gereği)

Bu projenin geliştirilmesinde Claude (Anthropic) kod üretimi, mimari planlama ve veri
analizi için kullanılmıştır. Katkı düzeyi: backend mimarisi, anomali tespit algoritması,
sentetik veri üretimi, Modbus/SCADA entegrasyonu ve frontend dashboard kodunun büyük
kısmı AI ile birlikte, takımın yönlendirmesi ve gerçek zamanlı test/doğrulamasıyla
geliştirilmiştir. Kalibrasyon deneyleri (docs/kalibrasyon.md) AI tarafından çalıştırılan
gerçek simülasyonlara dayanmaktadır, varsayımsal rakamlar değildir.

## Önceki benzer proje beyanı (Taahhütname Madde 4 gereği)

Takım üyesi Adam Mammadov, farklı bir problem alanında (dağıtım şebekesi kayıp/anomali
tespiti) "GridPulse" adlı bir projeyi SOCAR Smart Urbanization Capstone Program
kapsamında geliştirmiştir (kamuya açık, LinkedIn'de paylaşılmıştır). PanoPulse, o
projeden yalnızca genel mühendislik yaklaşımını (z-score + persistence filter tabanlı
anomali tespiti) miras almıştır — kod tabanı, veri modelleri ve problem alanı tamamen
farklı ve bu hackathon için sıfırdan yazılmıştır.

