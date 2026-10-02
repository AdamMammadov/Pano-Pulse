# Fiziki modul konsepti və sensor seçimi

## 1. Niyə LoRa, niyə BLE/Zigbee yox

AG pano/OG hücrə **metal mahfaza**dır (TEDAŞ-MLZ/2003-06.B şərtnaməsinə görə). Metal
mahfaza Faraday qəfəsi effekti yaradır və radio siqnalını əhəmiyyətli dərəcədə
zəiflədir — bu effekt tezlik artdıqca güclənir. Nəticədə:

| Texnologiya | Tezlik | Metal mahfazada performans |
|---|---|---|
| BLE | 2.4 GHz | Zəif — bir neçə metrdə belə etibarsız ola bilər |
| Zigbee | 2.4 GHz | BLE ilə eyni problem, mesh olsa da tezlik eyni |
| **LoRa** | **868 MHz (EU)** | **Xeyli yaxşı nüfuzetmə, sənaye mühitləri üçün nəzərdə tutulub** |
| NB-IoT/LTE-M | ~800-900 MHz | Yaxşı nüfuzetmə, amma operator şəbəkəsindən keçir (on-prem tələbinə uyğun deyil) |

Bu səbəbdən **LoRa**-nı seçdik — həm tezlik baxımından metal mahfazaya daha uyğun,
həm də (NB-IoT-dan fərqli olaraq) **tam yerli/on-prem** işləyə bilər: LoRa
gateway-i yerli şəbəkəyə qoşulur, data heç vaxt operator və ya ictimai internetdən
keçmir. LoRaWAN şəbəkə serverini özümüz yerli qururuq (məs. açıq mənbəli
ChirpStack, on-prem) — ictimai LoRaWAN provayderindən (The Things Network kimi)
istifadə etmirik, çünki bu, "Public Cloud yoxdur" tələbinə ziddir.

## 2. Seçilən sensor: Dragino LHT65N

Konkret, bazarda mövcud bir məhsulu nümunə göstəririk (tam istehsalçı seçimi
son qərar deyil, konsepti sübut etmək üçündür):

- **Daxili temperatur/nəm sensoru**: ətraf mühiti (`ambient_temp_C`, `humidity_pct`) ölçür
- **Xarici prob girişi**: kabelə/baraya bilavasitə bərkidilən xarici temperatur
  probu (DS18B20 və ya daha dəqiq TMP117A variantı) — bu, bizim `surface_temp_C`
  kanalımızın tam qarşılığıdır, yəni **bir cihazla iki kanalı da əldə edirik**
- **Enerji**: daxili 2400mAh batareya, hesabat intervalından asılı olaraq
  bir neçə ilə qədər (istehsalçı 10 ilə qədər iddia edir, real ömür göndərmə
  tezliyinə görə dəyişir) — "bakım gerektirmeyen" tələbinə uyğun
- **Qoruma sinfi**: IP65 — nəmli/tozlu pano mühiti üçün kifayətdir
- **Quraşdırma**: tam "tak-çalıştır" — yeni naqil çəkilmir, mövcud kabel
  yığınına toxunmur, sadəcə DIN-ray və ya yapışqanlı əsaslıqla bərkidilir

## 3. Yerləşdirmə

TEDAŞ texniki çiziminə görə (EK-II/14), 1600 kVA pano 1600×1500×450mm ölçüsündədir
və üstündə artıq bir **"Modem" bölməsi** ayrılıb — gateway modulumuzu məhz bu
bölmədə, DIN-ray üzərində yerləşdiririk. Xarici antenna lazım olarsa, mövcud
kabel keçidlərindən istifadə edilə bilər, yeni deşik açmağa ehtiyac yoxdur.

Sensor düyünü (LHT65N) isə ölçüləcək nöqtəyə (məs. əsas bara birləşməsi
yaxınlığı) sərbəst yerləşdirilir — naqilsiz olduğu üçün yerini seçməkdə
sərbəstlik var, yalnız gateway-in LoRa əhatəsində olması kifayətdir (bir neçə
on metr, mahfaza daxilində belə).

## 4. Gateway modulunun blok sxemi

(Bax: yuxarıdakı diaqram — "panopulse_gateway_pcb_block_diagram")

Qısaca: ESP32-S3 mərkəzi emal vahidi, RS-485 transceiver ilə mövcud ABB TVOC-2
və MPR-53CS cihazlarını Modbus RTU master kimi oxuyur, LoRa alıcısı ilə
kablosuz temp/nəm düyününü dinləyir, Ethernet ilə yerli PanoPulse serverinə
ötürür. Bütün komponentlər kommersiyaya hazır modullardır (heç biri xüsusi
istehsal tələb etmir) — bu, həm sürəti, həm dəyər/fayda nisbətini artırır.

## 5. Miqyaslana bilərlik

Hər pano üçün 1 gateway + 1 LHT65N düyünü lazımdır. 100+ pano üçün bu, sadəcə
təkrarlanan, eyni komponentli quraşdırmadır — xüsusi mühəndislik işi hər sahə
üçün təkrarlanmır, yalnız RS-485 ünvanı və LoRa cihaz ID-si fərqlənir.
