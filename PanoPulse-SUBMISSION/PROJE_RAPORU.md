# PanoPulse — Proje Raporu

**Pano/Hücre İçi Anomali Erken Uyarı Sistemi**
Grid Up Hackathon — ADM Elektrik & GDZ Elektrik
Takım #126 "Turquoise Hamster" — Adam Mammadov, Lala Shirinli

---

## 1. Problem Tanımı

Orta gerilim (OG) hücreleri ve alçak gerilim (AG) dağıtım panolarındaki arızaların
büyük çoğunluğu, gerçek arıza gerçekleşmeden önce ölçülebilir sinyaller verir:
aşırı ısınma, anormal akım dalgalanması, izolasyon zayıflaması, kısmi deşarj
artışı. Sorun, bu sinyallerin çoğu zaman ayrı ayrı izlenmesi, birbiriyle
ilişkilendirilmemesi ve dolayısıyla arıza gerçekleşene kadar fark edilmemesidir.

Grid Up Hackathon'un bu göreve özel beklentileri: kablosuz/tak-çalıştır sensör
mimarisi, yalnızca yerinde (on-prem) çalışma — genel bulut bağımlılığı olmaması,
mevcut SCADA altyapısıyla Modbus üzerinden entegrasyon, SMS/WhatsApp bildirim
kanalı, en az 100 modüllük ölçeklenebilirlik ve gerçek veya sentetik veriyle
gösterim.

## 2. Çözüm Yaklaşımı

PanoPulse, dört farklı sensör kanalından (akım, yüzey/ortam sıcaklığı-nem,
kısmi deşarj, ARC) gelen veriyi tek bir risk füzyon motorunda birleştirir.
Tek bir kanaldaki anlık sapmaya güvenmek yerine:

- Her kanal için istatistiksel sapma (z-score) hesaplanır;
- Bir sinyalin "gerçek" sayılması için ardışık birden çok örnekte aynı eğilim
  doğrulanmalıdır (persistence filter) — bu, tek seferlik gürültüyü gerçek bir
  eğilimden ayırır;
- Birden fazla kanal aynı anda sapma gösterdiğinde (örn. akım + sıcaklık),
  sistem bunu çok daha yüksek güvenle gerçek bir anomali olarak değerlendirir
  ve olası nedeni yüzdelik olasılık dağılımıyla sunar;
- Yüzey sıcaklığı trendinin doğrusal ekstrapolasyonu ile, kritik eşiğe kaç
  saat/dakika kaldığı tahmin edilir (kestirimci bakım).

ARC (ark flaşı) tespiti bilinçli olarak farklı ele alınmıştır: ABB TVOC-2
zaten SIL-2 sertifikalı, <1ms tepki süreli bir tetikleme sistemidir. Bu
sertifikalı güvenlik cihazının üzerine "daha akıllı" bir ML modeli
kurulmamış, onun durumu doğrudan en yüksek öncelikle yansıtılmıştır — bu,
gereksiz karmaşıklık yerine mühendislik disiplinini yansıtan bilinçli bir
tercihtir.

## 3. Sistem Mimarisi

```
Sensörler (Akım / ARC / PD / Sıcaklık-Nem)
                    ↓
   Yerel gateway (Modbus master, ESP32-S3 mikrodenetleyici konsepti)
                    ↓
   On-prem risk füzyon motoru (bu depo — anomaly_engine.py)
                    ↓
   ┌──────────┬──────────┬─────────────┬────────────────┐
SCADA/Modbus  Dashboard  SMS/WhatsApp/  AI Co-Pilot
(port 5020)   (React)    Telegram        (sadece gerçek veriye
                                          dayalı, halüsinasyon yok)
```

**Backend**: Python + FastAPI. **Frontend**: React + Vite. **Kalıcılık**:
SQLite (yerel, bulut bağımlılığı yok). **SCADA entegrasyonu**: gerçek,
çalışan bir Modbus TCP server (port 5020) — bağımsız bir Modbus istemcisiyle
doğrulanmıştır.

## 4. Öne Çıkan Özellikler

**Tespit ve analiz**

- Ampirik olarak kalibre edilmiş anomali motoru: yanlış alarm oranı
  1.87 → 0.024/pano/gün (78 kat iyileşme), gerçek tespit hızında yalnızca
  ~1 dakikalık maliyetle (bkz. `docs/kalibrasyon.md`)
- Kök-neden yüzdelik olasılık dağılımı (örn. "Gevşek klemens — %52,
  Aşırı yüklenme — %48")
- Kestirimci bakım: canlı, saniye saniye işleyen geri sayım sayacı
  (ör. "Kritik eşiğe 00:41:59")
- 120 panoluk (>100 gereksinimini karşılayan) eş zamanlı canlı simülasyon

**Gerçek donanım/protokol entegrasyonu**

- Çalışan Modbus TCP SCADA server'ı (port 5020) — organizatörün istediği
  SCADA entegrasyon gereksinimini karşılar
- AG-001 panosu için **gerçek bir Modbus master/slave round-trip**: sanal
  MPR-53CS ve ABB TVOC-2 cihazları, organizatörün paylaştığı resmi register
  haritalarıyla birebir uyumlu şekilde simüle edilir ve gerçek bir Modbus
  istemcisiyle sorgulanır. Bu entegrasyon başlangıçta kararsızdı; takım
  üyesi Lala Shirinli'nin bağımsız araştırmasıyla kök nedenler (asenkron
  kütüphane kararsızlığı, register taşması) bulunup düzeltilmiş, entegrasyon
  45 saniyelik tekrarlı testte %100 başarıyla doğrulanmıştır

**Yapay zeka**

- AI Co-Pilot: yalnızca panonun gerçek, o anki verisine dayanan doğal dil
  arayüzü — halüsinasyon yapmaz, uydurma teknik değer (tork, amper limiti
  vb.) vermez (bu, sahada gerçek zarara yol açabileceği için bilinçli bir
  tasarım kararıdır)
- Otomatik PDF inceleme raporu (`GET /cabinets/{id}/report.pdf`) — risk
  skoru, kök neden, kestirimci bakım ve ekipman/standart referanslarını içerir

**Karar destek ve analiz araçları**

- **What-If Simulator**: "Nem %20 artarsa risk nasıl değişir?" tarzı sorulara,
  gerçek tespit motorunun ÜZERİNDE, hiçbir canlı veriyi değiştirmeden anlık
  cevap verir (read-only projeksiyon, otomatik testlerle korunur)
- **Cabinet Health Score**: anlık risk skorundan ayrı, uzun vadeli güvenilirlik
  göstergesi — tekrarlayan anomaliler zamanla düşürür, mevcut an normal
  görünse bile panonun genel "sağlık" durumunu yansıtır
- **Top Priority Panels**: sadece risk skoruna göre değil, risk + kalıcılık
  (persistence) + tahmin aciliyetinin ağırlıklı formülüyle sıralanan öncelik
  listesi — operatöre "önce hangisine bakmalıyım?" sorusunun cevabını verir
- **Digital Forensics / Olay Zaman Çizelgesi**: her anomali anının tam sensör
  görüntüsüyle (kanıt olarak) saklanması — bir alarmın "neden" olduğunu
  geriye dönük, veriye dayalı şekilde gösterir
- **Risk Heatmap**: 120 panonun substation düzeninde, tek bakışta genel
  durumu gösteren ızgara görünümü

**İş sürekliliği ve saha entegrasyonu**

- SMS / WhatsApp / Telegram bildirim kanalları (yerel gateway mimarisiyle,
  gerçek Telegram Bot API entegrasyonu dahil)
- Maliyet Etki ve Enerji Verimliliği (ESG) hesaplayıcıları — sabit, uydurma
  rakamlar yerine gerçek model çıktısına (kestirimci bakım süresi) ve
  şeffaf, düzenlenebilir varsayımlara (P=I²R formülü) dayanır
- Otonom Savunma (Auto-Trip) kavram gösterimi — risk %90'ı aştığında, açıkça
  "SİMÜLASYON" etiketiyle sunulan, tam ekran bir önleyici yük atma senaryosu
  (Emergency Mode: ACKNOWLEDGE / VIEW INCIDENT / CREATE WORK ORDER)

**Sunum ve kullanıcı deneyimi**

- Tam otomatik "Canlı Sunum Modu" — tek düğmeyle, ~40 saniyelik uçtan uca
  senaryo (normal → anomali → gerçek zamanlı AI tespiti → iş emri → toparlanma)
- Filo Genel Bakış: Sistem Sağlığı göstergesi, Risk Heatmap, öncelik sıralı
  pano listesi, filo geneli tahmini mali risk, tek düğmeyle çoklu-pano
  simülasyonu
- Digital Twin: panonun canlı, renk kodlu şematik kesiti
- 20 otomatik test (pytest), hepsi yeşil

## 5. Kurulum ve Çalıştırma

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000
cd frontend && npm install && npm run dev
```

Dashboard: `http://localhost:5173` · API: `http://localhost:8000` ·
Modbus TCP: `localhost:5020`. Ayrıntılı komutlar ve test talimatları için
bkz. `README.md`.

## 6. Dürüst Sınırlamalar

- Docker build bu geliştirme ortamında tam doğrulanamadı (`docker-compose.yml`
  sözdizimi doğrulandı, gerçek makinede tam çalıştırma önerilir)
- Kısmi deşarj (PD) verisi sentetiktir — gerçek Techimp analizör çıktı
  formatı entegre edilmemiştir
- Kullanıcı seviyeli kimlik doğrulama yoktur (API anahtarı var, AD/LDAP yok)
- AR saha mühendisi arayüzü yalnızca bir konsept önizlemesidir, çalışan bir
  özellik değildir — arayüzde bu açıkça belirtilir

Bu sınırlamaların açıkça belirtilmesi, projenin eksikliği değil, ekibin
mühendislik yaklaşımının bir parçasıdır: her iddia gerçek bir ölçüme veya
teste dayanmaktadır, hiçbir sayı veya durum abartılmamıştır.

## 7. Yapay Zeka Kullanımı Beyanı (Taahhütname Madde 4 gereği)

Bu projenin geliştirilmesinde Claude (Anthropic) kod üretimi, mimari planlama
ve veri analizi için kullanılmıştır. Backend mimarisi, anomali tespit
algoritması, sentetik veri üretimi, Modbus/SCADA entegrasyonu ve frontend
dashboard kodunun büyük kısmı AI ile birlikte, takımın yönlendirmesi ve
gerçek zamanlı test/doğrulamasıyla geliştirilmiştir. Kalibrasyon deneyleri
gerçek simülasyonlara dayanmaktadır, varsayımsal rakamlar değildir. Ayrıntılı
katkı dökümü için bkz. `README.md`.

## 8. Önceki Benzer Proje Beyanı (Taahhütname Madde 4 gereği)

Takım üyesi Adam Mammadov, farklı bir problem alanında (dağıtım şebekesi
kayıp/anomali tespiti) "GridPulse" adlı bir projeyi SOCAR Smart Urbanization
Capstone Program kapsamında geliştirmiştir. PanoPulse, o projeden yalnızca
genel mühendislik yaklaşımını (z-score + persistence filter tabanlı anomali
tespiti) miras almıştır — kod tabanı, veri modelleri ve problem alanı
tamamen farklı ve bu hackathon için sıfırdan yazılmıştır.
