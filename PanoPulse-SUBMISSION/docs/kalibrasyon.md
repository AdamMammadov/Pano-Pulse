# Kalibrasyon: yanlış alarm oranının azaldılması

GridPulse'un kendi tuning tarihçesinden (v1→v5, ham z-score'un tek başına
kullanılamayacağı dersi) yola çıkarak, PanoPulse'u devreye almadan önce
120 panoluk filo ölçeğinde ampirik olarak test ettik.

## Yöntem

120 panoyu, hiçbir anomali senaryosu tetiklenmeden, yalnızca `Scenario.NORMAL`
altında ~8.3 saat (500 tick × 60sn) simüle ettik ve kaç "yanlış" alarmın
ateşlendiğini saydık (`backend/app/anomaly_engine.py` ile aynı mantık,
tekrarlanabilir script `docs/_kalibrasyon_scripti.py` değil — doğrudan
`CabinetEngine` sınıfı üzerinden çalıştırıldı).

## Sonuçlar

| Versiyon | Z eşiği | Persistence | Mantık | Yanlış alarm / pano / gün |
|---|---|---|---|---|
| v1 | 2.0 | 3 | leaky (azalan sayaç) | **2.88** |
| v2 | 2.0 | 3 | strict (ardışık, sıfırlanan) | 2.16 |
| v3 | 2.5 | 4 | strict (ardışık, sıfırlanan) | **0.024** ✅ |

**v3 benimsendi.** 120 panoluk bir filoda bu, günde ~3 yanlış alarm demektir
(120 × 0.024 ≈ 2.9) — 1. versiyondaki ~345 yanlış alarm/gün ile
karşılaştırıldığında, operasyon ekibinin güvenip kullanabileceği bir seviye.

## Bunun gerçek tespit hızına maliyeti

| Senaryo | v1 (Z=2.0, p=3) | v3 (Z=2.5, p=4) | Fark |
|---|---|---|---|
| Aşırı yüklenme | 3 dk | 4 dk | +1 dk |
| İzolasyon bozulması | 4 dk | 5 dk | +1 dk |
| Ark flaşı | anlık (ABB TVOC-2 trip) | anlık | değişmez |
| Sensör arızası | anlık (link kaybı) | anlık | değişmez |

Sonuç: **yanlış alarmda ~78 kat iyileşme, gerçek tespitte yalnızca ~1 dakika
gecikme.** Bu takas, sahada güvenilirliği doğrudan operasyon ekibinin alarmlara
güvenip güvenmeyeceğini belirlediği için bilinçli olarak yapıldı.

## Neden "leaky" sayaç yeterli değildi

İlk tasarımda streak sayacı her anomali-dışı örnekte 1 azalıyordu (0'a kadar).
Bu, sık ama düzensiz sapmaların zamanla sayaç üzerinde birikmesine izin
veriyordu — yani "3 ardışık" değil, "son birkaç düzine örnekte net 3 fazla
sapma" gibi davranıyordu. Sıkı (strict) versiyon, herhangi bir normal
okumada sayacı sıfırlayarak gerçek, kesintisiz bir eğilim arıyor — bu da
tam olarak "kritik arıza gerçekleşmeden önce" beklenen kalıcı, artan bir
sinyaldir; tek seferlik gürültü değil.
# Modbus Cihaz Entegrasyonu ve Bağlantı Kararlılığı Araştırması

## 1. Problem Tanımı
`device_process.py` (Modbus Server) ve `bridge_process.py` (Modbus Client) arasındaki asenkron (`pymodbus`) haberleşmede, isteklerin yanıtsız kalması ve hiçbir hata vermeden sürecin kilitlenmesi sorunu incelenmiştir.

## 2. Denenen Yaklaşımlar ve Testler
* **Asenkron Yapı:** `pymodbus` kütüphanesinin `asyncio` altyapısı, soketlerin kilitlenmesine ve event loop'un askıda kalmasına neden olmaktaydı.
* **Senkron Yapıya Geçiş:** Asenkron yaklaşım yerine daha hafif ve kararlı olan senkron `pyModbusTCP` kütüphanesine geçildi.
* **Kalıcı Bağlantı ve Zaman Aşımı:** Soketleri her istekte yeniden açmak yerine kalıcı bağlantı (`auto_open=True`) sağlandı ve 2.0 saniyelik zaman aşımı (`timeout=2.0`) eklendi.

## 3. Sonuç ve Elde Edilen Verim
Sistem senkron `pyModbusTCP` yapısına geçirildikten sonra MPR-53CS (Port 5031) ve ABB TVOC-2 (Port 5032) cihazlarından gelen veriler donma veya kesinti olmadan kararlı şekilde okunmaya başlanmıştır.
# Modbus Cihaz Entegrasyonu ve Bağlantı Kararlılığı Araştırması

## Yapılan Çalışmalar

* Projedeki `MPR-53CS` ve `TVOC-2` Modbus TCP cihazlarının bağlantısı incelendi.
* `device_process.py`, `bridge_process.py`, `main.py` ve `modbus_server.py` dosyaları kontrol edildi.
* Modbus bağlantısı hem `pymodbus` hem de `pyModbusTCP` ile test edildi.
* MPR-53CS için L1, L2 ve L3 register adresleri kontrol edildi:

  * L1 → `6`
  * L2 → `8`
  * L3 → `10`
* İlk testlerde register okuma hataları gözlemlendi.
* Akım değerlerinin `×1000` ile register'a yazılması durumunda değerlerin `uint16` sınırını (`65535`) aşabildiği tespit edildi.
* Geçici olarak `×1` ölçeklendirme ile test yapıldı ve Modbus okumalarının başarılı olduğu görüldü.
* Tekrarlı testlerde MPR-53CS ve TVOC-2 bağlantılarının başarılı olduğu ve `failed=0` sonucu alındığı doğrulandı.
* FastAPI backend'in çalışması ve `/health`, `/cabinets`, `/modbus/register-map` gibi endpoint'ler kontrol edildi.
* Projede 120 cabinet'in API üzerinden oluşturulduğu doğrulandı.
* PanoPulse'un kendi Modbus SCADA server'ının `5020` portunda çalıştığı ve register formatında `×10` ölçeklendirme kullandığı görüldü.
* Ayrıca `device_process.py` ve `bridge_process.py` dosyalarının aynı Modbus portlarını (`5031`, `5032`) açmaya çalıştığı tespit edildi. Bu durum mimarinin ayrıca incelenmesi gerektiğini gösterdi.
* Çalışma sonunda çalışan Python process'leri durduruldu ve `5031`, `5032`, `5020`, `8000` portlarında aktif `LISTENING` bağlantısı kalmadığı doğrulandı.

## Sonuç

Modbus TCP bağlantısının temel olarak çalıştığı doğrulandı. İlk okuma probleminin önemli nedenlerinden biri register'a yazılan akım değerlerinin `uint16` sınırını aşmasıdır.

Ancak nihai register ölçeklendirmesi ve `device_process → bridge_process → SQLite → main.py → Modbus 5020` veri akışının doğru şekilde kurulması henüz tamamlanmamıştır.

## Sonraki Adımlar

1. `storage.py` ve `field_gateway_state` yapısını incelemek.
2. `bridge_process.py`'in gerçek görevini netleştirmek.
3. MPR-53CS için doğru register ölçeklendirmesini kesinleştirmek.
4. Device → Bridge → SQLite → API → Modbus 5020 uçtan uca testi yapmak.

# Sonraki Çalışmalar ve Güncel Durum

Önceki araştırmada belirtilen eksik noktalar üzerinde ek çalışmalar yapılmıştır.

## Modbus Cihaz ve Bridge Mimarisi

`device_process.py` ve `bridge_process.py` arasındaki görev dağılımı netleştirilmiştir:

* `device_process.py` → Modbus TCP Server
* `bridge_process.py` → Modbus TCP Client

MPR-53CS cihazı `5031` portundan, ABB TVOC-2 cihazı ise `5032` portundan çalışmaktadır.

`bridge_process.py`, cihazlara client olarak bağlanarak register değerlerini okumaktadır.

## Modbus Haberleşmesinin Stabilizasyonu

İlk testlerde kullanılan asenkron `pymodbus` yapısında bağlantıların zaman zaman yanıtsız kalması ve sürecin askıda kalması gözlemlenmiştir.

Bu nedenle bridge tarafı senkron `pyModbusTCP` yapısına geçirilmiştir.

Bağlantı ayarlarında:

* `auto_open=True`
* `auto_close=False`
* `timeout=2.0`

kullanılmıştır.

Bu değişiklikten sonra MPR-53CS ve ABB TVOC-2 cihazlarından tekrarlı ve kararlı şekilde veri okunmuştur.

## Register Okumaları

MPR-53CS için:

* L1 → register `6`
* L2 → register `8`
* L3 → register `10`

ABB TVOC-2 için:

* TRIP → register `100`
* SYSTEM_STATE → register `1300`

register'ları başarıyla okunmuştur.

Tekrarlı testlerde `failed=0` sonucu elde edilmiştir.

## SQLite Veri Aktarımı

Bridge tarafından okunan son Modbus değerleri `backend/panopulse.db` içerisindeki `field_gateway_state` tablosuna yazılacak şekilde yapılandırılmıştır.

Tabloda aşağıdaki bilgiler tutulmaktadır:

* `cabinet_id`
* `ts`
* `current_l1`
* `current_l2`
* `current_l3`
* `arc_trip`
* `arc_system_state`
* `link_ok`

Böylece Modbus cihazlarından alınan veriler bridge üzerinden SQLite veri katmanına aktarılmaktadır.

## Güncel Veri Akışı

Güncel yapı:

`MPR-53CS / ABB TVOC-2 → bridge_process.py → SQLite (field_gateway_state)`

Test sırasında bridge'in cihazlardan başarılı şekilde veri aldığı ve SQLite'a güncel değerleri yazdığı doğrulanmıştır.

Örnek testlerde:

`success` değeri artmış, `failed=0` olarak kalmıştır.

Bu çalışmalar sonucunda daha önce açık kalan Modbus cihaz → bridge → SQLite veri aktarımı tamamlanmış ve doğrulanmıştır.


## Editöryal not: entegrasyonun son durumu (17 Eylül)

Yukarıdaki araştırma sonucunda bulunan iki düzeltme (senkron `pyModbusTCP`'ye
geçiş, `device_process.py`'deki ×1000 register taşması) ana kod tabanına
entegre edilmiştir. Entegrasyon sırasında ayrıca şu iki nokta düzeltilmiştir:

- **Ölçek uyuşmazlığı**: `device_process.py` artık ×1000 yapmadığı için,
  `bridge_process.py`'nin okuma tarafındaki `/1000` işlemi de kaldırıldı —
  aksi halde akım değerleri 1000 kat düşük okunurdu.
- **`link_ok` artık gerçek**: önceki taslakta bu alan sabit `1` yazılıyordu
  (okuma başarısız olsa bile). Artık yalnızca HER İKİ cihazdan da o turda
  gerçekten başarılı okuma alındıysa `1` yazılıyor.

Bu düzeltmelerden sonra AG-001 paneli, 45 saniyelik tekrarlı testte 8/8
başarı oranıyla gerçek "modbus_live" verisi göstermiştir (dashboard'da
🔌 rozeti). Bu, projedeki en zor teknik hedeflerden biriydi ve takım
üyesi Lala Shirinli'nin bağımsız araştırması sayesinde tamamlanmıştır.
