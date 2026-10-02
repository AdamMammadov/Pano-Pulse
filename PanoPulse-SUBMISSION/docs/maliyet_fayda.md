# Maliyət/fayda təhlili

Jüri qiymətləndirmə kriteriyalarında açıq yazılıb: *"harcamış olduğunuz
maliyet buna değer mi?"* Rəqəmləri şəffaf şəkildə ortaya qoyuruq —
dəqiq təchizatçı təklifi deyil, sifariş həcminə görə dəyişən **bazar
araşdırmasına əsaslanan təxmini aralıqlardır**.

## Pano-başına təxmini xərc (donanım)

| Komponent | Təxmini qiymət (ədəd) |
|---|---|
| MCU (ESP32-S3 development board) | $5–10 |
| RS-485 transceiver modulu | $2–5 |
| Kablosuz temp/nəm sensoru (Dragino LHT65N tipli) | ~$35–45 |
| Mühafizə/DIN-ray aksesuarları | $15–30 |
| **Cəmi (pano başına)** | **~$60–90** |

Paylaşılan infrastruktur (bir neçə on pano üçün ortaq):
- LoRa gateway (yerli, on-prem): ~$70–150 (məs. tək kanallı açıq mənbəli
  gateway sinfi), **20-50 pano arasında bölüşdürülür** → panoya düşən
  pay $2–8 arasında əlavə olunur

**Cəmi, pano başına: ~$65–100** (ilkin quraşdırma), sonrakı illik xərc
demək olar sıfır (batareya 5+ il, heç bir abunə haqqı — LoRaWAN yerli/
on-prem olduğu üçün operator haqqı yoxdur).

## Müqayisə nöqtəsi

1600 kVA-lıq bir AG panonun/OG hücrəsinin özü, avadanlıqları ilə birlikdə,
onbinlərlə dollar dəyərindədir. Pano-başına ~$70-100-lük bir erkən
xəbərdarlıq investisiyası, panonun öz dəyərinin **bində biri**
səviyyəsindədir.

Nəzərə alınmalı (spesifik rəqəm iddia etmədən, kateqoriya olaraq):
- **Avadanlıq zərəri**: ark flaşı hadisələri adətən yalnız bir cihazı
  deyil, bütün panonu/hücrəni zədələyir — dəyişdirmə xərci və tədarük
  müddəti əhəmiyyətlidir.
- **Kəsinti müddəti**: planlaşdırılmamış kəsinti, planlı baxımdan qat-qat
  bahalıdır (abunəçi sayı × kəsinti müddəti × tənzimləyici cərimə riski).
- **Təhlükəsizlik**: ark flaşı insan həyatına birbaşa təhdiddir — bu,
  maliyyə tərəfindən asılı olmayan, öz-özlüyündə üstün prioritetdir.

## Nəticə

Sistemin dəyəri, qarşısını aldığı **tək bir ciddi hadisənin** dəyərindən
qat-qat aşağıdır — hətta yalnız ölçeklənə bilən, aşağı-xərcli komponent
seçimi (kommersiyaya hazır, xüsusi istehsal tələb etməyən hissələr)
sayəsində 100+ panoya tətbiq belə əlçatan qalır.
