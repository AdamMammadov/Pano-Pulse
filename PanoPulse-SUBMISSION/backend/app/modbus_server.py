"""
PanoPulse — Modbus TCP server (SCADA entegrasyon katmanı)
--------------------------------------------------------------
Organizatörün kendi tavsiyesi: "Modbus register'ı seçtik biz, haritalama
şablonunu paylaştık" (açılış yayını, 10 Eyl) ve taahhütname: gerçek saha
sistemlerine bağlantı beklenmiyor, yaklaşımın gösterilmesi yeterli.

Bu modül PanoPulse'u bizzat bir Modbus TCP SLAVE (server) yapar — yani
ADM/GDZ'nin mevcut SCADA/RTU'su, MPR-53CS'i okuduğu AYNI Modbus
protokolüyle, ayrı bir kurulum gerektirmeden PanoPulse'un ürettiği füzyon
sonuçlarını (risk skoru, sensör değerleri, alarm bitleri) okuyabilir.
Yani entegrasyon yükü SCADA tarafında sıfır — sadece bir slave adresi.

Register haritası (pano başına 20 register bloğu, taban adres
1000 + (pano_no-1)*20). Tüm değerler x10 ölçekli unsigned 16-bit
(örn. 78.4A -> 784), MPR-53CS dokümanındaki "multiplier" kuralının
aynısı.

  offset  ad                         birim
  0       risk_score_x10             0-1000 (0-100.0)
  1       risk_label_code            0=normal 1=izlemede 2=uyarı 3=kritik
  2       current_L1_x10             A
  3       current_L2_x10             A
  4       current_L3_x10             A
  5       surface_temp_x10           °C
  6       ambient_temp_x10           °C
  7       humidity_x10               %RH
  8       pd_magnitude_x10           pC
  9       pd_pulses_x10              adet/çevrim
  10      arc_trip                   0/1
  11      arc_system_state           TVOC-2 "System state" kodu
  12      arc_link_ok                0/1
  13      alarm_active               0/1 (warning veya critical)
  14-15   timestamp (hi,lo)          Unix epoch, 32-bit böünmüş
  16-19   (reserved)

Gerçek dünyada bu modül RS-485 üzerinden TVOC-2 ve MPR-53CS'i MASTER
olarak okur (bkz. sensors.py'nin temsil ettiği katman); burada ise aynı
füzyon çıktısını SCADA'ya SLAVE olarak sunuyoruz — iki yönün de
Modbus olması, tek bir protokol yığınıyla uçtan uca gitmemizi sağlıyor.
"""
from __future__ import annotations
import asyncio
import time
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server import StartAsyncTcpServer

REGS_PER_CABINET = 20
BASE_ADDRESS = 1000
TOTAL_REGISTERS = 1000 + 200 * REGS_PER_CABINET  # headroom for 200 cabinets
MODBUS_PORT = 5020  # dev default; use 502 with elevated privileges in production

RISK_LABEL_CODE = {"normal": 0, "watch": 1, "warning": 2, "critical": 3}


def cabinet_base_address(index_1based: int) -> int:
    return BASE_ADDRESS + (index_1based - 1) * REGS_PER_CABINET


def _x10(v: float) -> int:
    return max(0, min(65535, round(v * 10)))


def encode_cabinet(snapshot: dict) -> list[int]:
    """Turns one CabinetEngine snapshot into its 20-register Modbus block."""
    ts = snapshot["timestamp"]
    epoch = int(ts.timestamp()) if hasattr(ts, "timestamp") else int(time.time())
    values = [0] * REGS_PER_CABINET
    values[0] = _x10(snapshot["risk_score"])
    values[1] = RISK_LABEL_CODE.get(snapshot["risk_label"], 0)
    values[2] = _x10(snapshot["current"]["L1"]["primary_A"])
    values[3] = _x10(snapshot["current"]["L2"]["primary_A"])
    values[4] = _x10(snapshot["current"]["L3"]["primary_A"])
    values[5] = _x10(snapshot["surface_temp_C"])
    values[6] = _x10(snapshot["ambient_temp_C"])
    values[7] = _x10(snapshot["humidity_pct"])
    values[8] = _x10(snapshot["pd_magnitude_pC"])
    values[9] = _x10(snapshot["pd_pulses_per_cycle"])
    values[10] = int(bool(snapshot["arc_trip"]))
    values[11] = int(snapshot["arc_system_state"])
    values[12] = int(bool(snapshot["arc_link_ok"]))
    values[13] = int(snapshot["risk_label"] in ("warning", "critical"))
    values[14] = (epoch >> 16) & 0xFFFF
    values[15] = epoch & 0xFFFF
    return values


def build_context() -> ModbusServerContext:
    hr_block = ModbusSequentialDataBlock(0, [0] * TOTAL_REGISTERS)
    slave = ModbusSlaveContext(hr=hr_block, zero_mode=True)
    return ModbusServerContext(slaves=slave, single=True)


async def sync_loop(context: ModbusServerContext, fleet, interval: float = 5.0):
    """Mirrors live fleet state into the Modbus register map on a timer —
    runs alongside the FastAPI app's own simulation loop."""
    slave = context[0]
    while True:
        for idx, cab in enumerate(fleet.cabinets.values(), start=1):
            if cab.latest:
                addr = cabinet_base_address(idx)
                slave.setValues(3, addr, encode_cabinet(cab.latest))
        await asyncio.sleep(interval)


async def start_modbus_server(fleet, host: str = "0.0.0.0", port: int = MODBUS_PORT):
    """Starts the Modbus TCP server + its sync loop as background tasks.
    Returns the created tasks so the caller can cancel them on shutdown
    (important for tests and clean restarts). Default port 5020 (not
    502) so it runs without root privileges during development; use
    502 with elevated privileges for a real deployment."""
    context = build_context()
    sync_task = asyncio.create_task(sync_loop(context, fleet))
    server_task = asyncio.create_task(StartAsyncTcpServer(context=context, address=(host, port)))
    return [sync_task, server_task]
