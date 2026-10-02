"""
PanoPulse — virtual saha cihazları (MPR-53CS + ABB TVOC-2)
--------------------------------------------------------------
⚠️ STATUS: HAZIRLANIB, AMMA CANLI TƏTBIQƏ QOŞULMAYIB.

İnteqrasiya sınağı zamanı, bu modulun serverləri əsas FastAPI
tətbiqinin (main.py) prosesi daxilində işə salınanda, pymodbus-un
asinxron klient oxumaları qeyri-sabit şəkildə (bəzən dərhal, bəzən heç
vaxt) asılı qalırdı. Kök səbəb tam təcrid oluna bilmədi — şübhələr:
(a) pydantic import sırası ilə pymodbus-un asyncio daxili strukturları
arasında konkret uyğunsuzluq, (b) 5031/5032 portlarında onlarla ardıcıl
debug dövründən yaranan soket vəziyyəti. Davamlı debug testlərində
nəticələr TƏKRARLANMADI (eyni test bəzən keçdi, bəzən asıldı) — bu,
"nadir hallarda uğursuz olan" bir inteqrasiyanı canlı təhvilə qoşmaqdan
daha pisdir, çünki demo zamanı gözlənilməz şəkildə asıla bilər.

Qərar: bu iki modul (bu fayl və field_gateway.py) TAM YAZILIB, DÜZGÜN
REGISTER ÜNVANLARI ilə (MPR-53CS: 6/8/10, TVOC-2: 100/1300 — bkz.
aşağı), və TƏK BAŞINA (asılı olmadan) sınanıb İŞLƏYİR (bkz. bu faylın
git tarixçəsindəki test nəticələri). Sadəcə 120-panolu əsas tətbiqin
event loop-u ilə birlikdə YÜZ FAİZ etibarlı olduğu sübut edilənə qədər
`main.py`-a qoşulmayıb. Növbəti addım: ayrıca bir proses/mikroservis
kimi işə salmaq (main.py ilə eyni event loop-u paylaşmadan) — bu, kök
səbəbi əhəmiyyətsizləşdirər.

Aşağıdakı kod məzmunu dəyişməyib, sadəcə main.py-dan import edilmir.
--------------------------------------------------------------
Bu modul, ADM/GDZ-nin bizə verdiyi RƏSMİ Modbus register sənədlərindəki
DƏQİQ ünvanları istifadə edərək iki virtual cihaz yaradır:

  MPR-53CS (enerji analizatoru) — mənbə: MPR-53CS_Modbus_Register_Map_EN.pdf
    Register 6  (0x0006): L1 Faz Cərəyanı, multiplier 0.001, Amper
    Register 8  (0x0008): L2 Faz Cərəyanı
    Register 10 (0x000A): L3 Faz Cərəyanı

  ABB TVOC-2 (Arc Guard) — mənbə: 1SFC170017M0201_Rev_D_TVOC-2_Modbus_Manual.pdf
    Register 100 (0x64): Trip 1 detector, low (X1:1–X2:5 bitfield)
    Register 149 (0x95): Number of trips
    Register 1200 (0x4B0): Modbus failure register
    Register 1300 (0x514): System state

Məqsəd: "biz sizin cihazlarınızın Modbus xəritəsini əzbərlədik" demək
əvəzinə, GERÇƏK ünvanlarla işləyən bir client/server cütü göstərmək.
Performans səbəbilə (120 ayrı TCP server demo prosesi üçün ağırdır) bu
tam round-trip yalnız AG-001 üçün canlıdır — arxitektura eynidir, sadəcə
demo miqyası məhduddur (bkz. main.py-dəki qeyd).
"""
from __future__ import annotations
import asyncio
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server import StartAsyncTcpServer

MPR53CS_PORT = 5031
TVOC2_PORT = 5032

# Real register offsets (bkz. yuxarı)
MPR_REG_L1, MPR_REG_L2, MPR_REG_L3 = 6, 8, 10
TVOC_REG_TRIP1_LOW, TVOC_REG_TRIP1_HIGH = 100, 101
TVOC_REG_NUM_TRIPS = 149
TVOC_REG_MODBUS_FAILURE = 1200
TVOC_REG_SYSTEM_STATE = 1300


def _new_context(size: int = 2000) -> ModbusServerContext:
    hr = ModbusSequentialDataBlock(0, [0] * size)
    return ModbusServerContext(slaves=ModbusSlaveContext(hr=hr, zero_mode=True), single=True)


class VirtualFieldDevices:
    """Fiziki 'yer üzü həqiqəti' — sənədləşdirilmiş register ünvanlarında
    canlı saxlanılan iki virtual Modbus slave. `push_truth()` hər tickdə
    çağırılır və gateway-in poll_* funksiyaları ilə OXUNACAQ dəyərləri
    bu context-lərə yazır (yəni bu, "cihazın özüdür", gateway isə ayrıca,
    field_gateway.py-də, bunu bir client kimi sorğulayır)."""

    def __init__(self):
        self.mpr_ctx = _new_context()
        self.tvoc_ctx = _new_context()

    def push_truth(self, current_A: dict, arc_trip: bool, num_trips: int):
        mpr = self.mpr_ctx[0]
        mpr.setValues(3, MPR_REG_L1, [round(current_A["L1"] * 1000)])
        mpr.setValues(3, MPR_REG_L2, [round(current_A["L2"] * 1000)])
        mpr.setValues(3, MPR_REG_L3, [round(current_A["L3"] * 1000)])

        tvoc = self.tvoc_ctx[0]
        tvoc.setValues(3, TVOC_REG_TRIP1_LOW, [1 if arc_trip else 0])
        tvoc.setValues(3, TVOC_REG_NUM_TRIPS, [num_trips])
        tvoc.setValues(3, TVOC_REG_MODBUS_FAILURE, [0])
        tvoc.setValues(3, TVOC_REG_SYSTEM_STATE, [2 if arc_trip else 0])

    async def start(self):
        t1 = asyncio.create_task(StartAsyncTcpServer(context=self.mpr_ctx, address=("127.0.0.1", MPR53CS_PORT)))
        t2 = asyncio.create_task(StartAsyncTcpServer(context=self.tvoc_ctx, address=("127.0.0.1", TVOC2_PORT)))
        return [t1, t2]
