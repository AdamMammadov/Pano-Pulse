# Demo video ssenarisi (ekran qeydiyyatı üçün)

Hədəf: 3-5 dəqiqəlik video. Hər addım üçün nə göstəriləcəyi və nə deyiləcəyi.

## 1. Açılış (15 san)
Dashboard-u aç. Sol paneldə 120 pano, hamısı yaşıl/normal.
> "PanoPulse, 100+ panonu real-vaxtda paralel izləyir. Hazırda hamısı normal."

## 2. Erkən xəbərdarlıq — Aşırı yüklənmə (45 san)
İstənilən panoda "Aşırı yüklenme" düyməsini bas. Risk qrafikinin canlı
yüksəldiyini göstər (3-4 dəqiqə simulyasiya = bir neçə saniyə real vaxt).
> "Sistem cərəyan artımını tək başına es keçmir — yüzey temperaturu ilə
> birlikdə qiymətləndirir. İkisi də eyni anda sapdıqda, bu 'gevşek bağlantı'
> siqnaturu kimi tanınır və kritik arıza baş verməmişdən ƏVVƏL xəbərdarlıq
> verilir." Sağ paneldəki alarmı göstər (SMS+WhatsApp kanalları).

## 3. Sertifikatlı təhlükəsizliyə hörmət — Ark flaşı (30 san)
Başqa bir panoda "Ark flaşı" düyməsini bas. Dərhal 100/kritik.
> "Ark aşkarlanması üçün öz modelimizi qurmuruq — ABB TVOC-2 artıq SIL-2
> sertifikatlı, 1ms-dən sürətli reaksiya verən bir sistemdir. Biz sadəcə
> onun trip siqnalını maksimum prioritetlə relay edirik."

## 4. İzolasiya bozulması — yavaş, sürünən risk (30 san)
Üçüncü panoda "İzolasyon bozulması" düyməsini bas.
> "Nəm və qismi boşalma birlikdə artdıqda, bu izolasiya zəifləməsinin erkən
> əlamətidir — aylarla əvvəl aşkarlana bilən bir tendensiyadır."

## 5. SCADA inteqrasiyası — canlı sübut (40 san)
Terminalda `modbus_server.py` ilə işə düşən Modbus TCP server-ə real bir
Modbus klientlə qoşulub register oxumağı göstər (əvvəlcədən hazırlanmış
`test_modbus_client.py` skripti ilə). Ekranda risk_score/arc_trip
registrlərinin dashboard-dakı ilə eyni olduğunu göstər.
> "Bu, simulyasiya deyil — real Modbus TCP protokolu ilə işləyən bir
> server. ADM/GDZ-nin mövcud SCADA-sı, MPR-53CS-i oxuduğu EYNİ üsulla
> bizim füzyon nəticələrimizi də oxuya bilər. Əlavə inteqrasiya işi yoxdur."

## 6. Fiziki konsept + miqyas (30 san)
Gateway blok sxemini və pano çizimini göstər.
> "Bütün komponentlər kommersiyaya hazır modullardır. LoRa seçimi, metal
> mahfazanın RF nüfuzetmə problemini həll etmək üçün bilərəkdən edilib."
Fleet xülasəsinə qayıt, 120 panonun paralel izləndiyini vurğula.

## 7. Bağlanış (10 san)
> "PanoPulse: sertifikatlı sistemlərə hörmət edən, on-prem, miqyaslana bilən
> və artıq SCADA ilə danışan bir erkən xəbərdarlıq platformasıdır."

---

## Texniki qeydlər (çəkilişdən əvvəl)
- Backend + frontend-i əvvəlcədən başlat, 15-20 saniyə isin ki, tarixçə dolsun.
- Ssenarini tetiklədikdən sonra ekранı 20-25 saniyə saxla ki, risk qrafiki
  görünəcək qədər yüksəlsin (real vaxtda ~4 tick × 5 saniyə = 20 saniyə).
- Video ixracını 480p/720p-də, sıxılmış (H.264) et — 10MB limitini keçməsin.
  Sığmasa, YouTube "unlisted" və ya Google Drive linkini PDF-ə yaz.
