"""
PanoPulse — virtual saha cihazları, AYRI PROSES olaraq
------------------------------------------------------------
Bu skript BİLƏRƏKDƏN minimal asılılıqla yazılıb: yalnız Python
standart kitabxanası + pymodbus. `app` paketindən (və dolayısıyla
FastAPI/pydantic-dən) HEÇ NƏ idxal etmir.

Səbəb: main.py-a birbaşa qoşulanda (eyni prosesdə, eyni event loop-da)
pymodbus-un asinxron server/klienti qeyri-sabit şəkildə asılırdı.
Kök səbəb tam təsdiqlənməsə də (pydantic import sırası şübhəli əsas
namizəddir), ən etibarlı həll onu TAMAMILƏ AYRI BİR PROSESDƏ
işlətməkdir — bu, həm problemi aradan qaldırır, HƏM DƏ arxitekturanı
REAL DÜNYAYA daha yaxın edir: TVOC-2 və MPR-53CS zatən ayrı, müstəqil
fiziki cihazlardır, bizim server prosesimizin bir hissəsi deyil.

İşə salınması: ayrıca, `python -m app.device_process` (main.py bunu
avtomatik subprocess olaraq başladır/bitirir, bkz. main.py).

Demo ssenarisini tetiklemek üçün: main.py, bu prosesin TVOC-2
register-inə (2000: FORCE_TRIP) Modbus WRITE (function code 6) ilə
yazır — bu proses də öz növbəsində bunu oxuyub arc trip simulyasiya
edir. Yəni idarəetmə də real Modbus protokolu üzərindən gedir.
"""
from __future__ import annotations
import asyncio
import math
import random
import time

from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server import StartAsyncTcpServer

MPR53CS_PORT = 5031
TVOC2_PORT = 5032

MPR_REG_L1, MPR_REG_L2, MPR_REG_L3 = 6, 8, 10
TVOC_REG_TRIP1_LOW = 100
TVOC_REG_NUM_TRIPS = 149
TVOC_REG_MODBUS_FAILURE = 1200
TVOC_REG_SYSTEM_STATE = 1300
TVOC_REG_FORCE_TRIP = 2000  # PanoPulse-a məxsus, sənədləşdirilməmiş "kontrol" registeri (demo üçün)


def _new_context(size: int) -> ModbusServerContext:
    hr = ModbusSequentialDataBlock(0, [0] * size)
    return ModbusServerContext(slaves=ModbusSlaveContext(hr=hr, zero_mode=True), single=True)


async def simulation_loop(mpr_ctx, tvoc_ctx):
    rng = random.Random(1)
    base = 250.0
    num_trips = 0
    was_tripped = False
    t0 = time.time()

    while True:
        elapsed_h = (time.time() - t0) / 3600 * 60  # sürətləndirilmiş demo saatı
        shape = 0.6 + 0.3 * math.sin(elapsed_h / 24 * 2 * math.pi)
        currents = {
            "L1": base * shape + rng.uniform(-5, 5),
            "L2": base * shape * 0.97 + rng.uniform(-5, 5),
            "L3": base * shape * 1.02 + rng.uniform(-5, 5),
        }

        force_trip = tvoc_ctx[0].getValues(3, TVOC_REG_FORCE_TRIP, count=1)[0]
        trip = bool(force_trip)
        if trip and not was_tripped:
            num_trips += 1
        was_tripped = trip

        mpr = mpr_ctx[0]
        mpr.setValues(3,MPR_REG_L1,[round(currents["L1"])])
        mpr.setValues(3,MPR_REG_L2,[round(currents["L2"])])
        mpr.setValues(3,MPR_REG_L3,[round(currents["L3"])])
        tvoc = tvoc_ctx[0]
        tvoc.setValues(3, TVOC_REG_TRIP1_LOW, [1 if trip else 0])
        tvoc.setValues(3, TVOC_REG_NUM_TRIPS, [num_trips])
        tvoc.setValues(3, TVOC_REG_MODBUS_FAILURE, [0])
        tvoc.setValues(3, TVOC_REG_SYSTEM_STATE, [2 if trip else 0])

        await asyncio.sleep(1)


async def main():
    mpr_ctx = _new_context(2000)
    tvoc_ctx = _new_context(3000)

    print(f"[device_process] MPR-53CS simülatörü: 127.0.0.1:{MPR53CS_PORT}", flush=True)
    print(f"[device_process] ABB TVOC-2 simülatörü: 127.0.0.1:{TVOC2_PORT}", flush=True)

    await asyncio.gather(
        StartAsyncTcpServer(context=mpr_ctx, address=("127.0.0.1", MPR53CS_PORT)),
        StartAsyncTcpServer(context=tvoc_ctx, address=("127.0.0.1", TVOC2_PORT)),
        simulation_loop(mpr_ctx, tvoc_ctx),
    )


if __name__ == "__main__":
    asyncio.run(main())
