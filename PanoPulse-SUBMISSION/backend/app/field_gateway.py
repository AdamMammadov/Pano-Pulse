"""
PanoPulse — sahə gateway-i (Modbus MASTER)
----------------------------------------------
Bu, RS-485 üzərində fiziki gateway-imizin (bkz. docs/fiziki_modul...)
edəcəyi işin bilgisayar üzərindəki eynisidir: MPR-53CS və ABB TVOC-2-ni
onların ÖZ, sənədləşdirilmiş register ünvanlarında Modbus client kimi
sorğulayır. `device_simulators.py`-dəki virtual cihazlarla birlikdə
işlədikdə, bu, uçdan-uca GERÇƏK bir Modbus round-trip-dir — heç bir
dəyər birbaşa "ötürülmür", hər dəfə şəbəkə üzərindən oxunur.

QEYD (mühəndislik dərsi): İlk versiya pymodbus-un SİNXRON (bloklayan)
клиентini bir asyncio tətbiqinin içində birbaşa çağırırdı. Bu, tək
thread-li event loop-u bloklayaraq öz-özünü kilidləyən (deadlock) bir
vəziyyət yaratdı — server tapşırığı heç vaxt cavab verə bilmirdi, çünki
eyni loop client çağırışında donub qalmışdı. Həll: pymodbus-un ASİNXRON
клиентinə keçmək — bu, digər bütün asyncio tapşırıqları (server daxil)
ilə düzgün əməkdaşlıq edir.
"""
from __future__ import annotations
from pymodbus.client import AsyncModbusTcpClient
from .device_simulators import (
    MPR53CS_PORT, TVOC2_PORT,
    MPR_REG_L1, MPR_REG_L2, MPR_REG_L3,
    TVOC_REG_TRIP1_LOW, TVOC_REG_SYSTEM_STATE,
)


async def poll_mpr53cs(host: str = "127.0.0.1", port: int = MPR53CS_PORT) -> dict | None:
    """MPR-53CS-i Modbus client kimi sorğulayır. Real cihazda RS-485
    üzərindən eyni funksiya kodu (03) və eyni ünvanlar istifadə edilir —
    burada yalnız nəqliyyat qatı (TCP vs RTU) fərqlidir."""
    client = AsyncModbusTcpClient(host, port=port)
    try:
        await client.connect()
        if not client.connected:
            return None
        rr = await client.read_holding_registers(MPR_REG_L1, count=5, slave=1)
        if rr.isError():
            return None
        regs = rr.registers
        return {
            "L1": regs[0] / 1000,  # register spec: multiplier 0.001
            "L2": regs[MPR_REG_L2 - MPR_REG_L1] / 1000,
            "L3": regs[MPR_REG_L3 - MPR_REG_L1] / 1000,
        }
    except Exception:
        return None
    finally:
        client.close()


async def poll_tvoc2(host: str = "127.0.0.1", port: int = TVOC2_PORT) -> dict:
    """ABB TVOC-2-ni sorğulayır: trip detector + system state. Oxuma
    uğursuz olarsa link_ok=False qaytarır — real sahədə bu, "Modbus
    failure register"-in özünün simptomu olardı."""
    client = AsyncModbusTcpClient(host, port=port)
    try:
        await client.connect()
        if not client.connected:
            return {"trip": False, "system_state": 0, "link_ok": False}
        rr = await client.read_holding_registers(TVOC_REG_TRIP1_LOW, count=1, slave=1)
        rs = await client.read_holding_registers(TVOC_REG_SYSTEM_STATE, count=1, slave=1)
        if rr.isError() or rs.isError():
            return {"trip": False, "system_state": 0, "link_ok": False}
        return {"trip": bool(rr.registers[0]), "system_state": rs.registers[0], "link_ok": True}
    except Exception:
        return {"trip": False, "system_state": 0, "link_ok": False}
    finally:
        client.close()


async def poll_all() -> dict:
    """Hər iki cihazı sorğulayıb, CabinetSimulator.advance()-un çıxışına
    uyğun formatda birləşdirir."""
    current = await poll_mpr53cs()
    arc = await poll_tvoc2()
    return {"current": current, "arc": arc}
