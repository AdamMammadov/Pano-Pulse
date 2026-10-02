"""
Demo helper — proves PanoPulse's Modbus TCP slave works with a real,
independent Modbus client (exactly what ADM/GDZ's SCADA would do).

Usage:
    python test_modbus_client.py [cabinet_number]

Run this while the backend (uvicorn app.main:app) is running.
"""
import sys
from pymodbus.client import ModbusTcpClient

BASE_ADDRESS = 1000
REGS_PER_CABINET = 20

FIELDS = [
    "risk_score_x10", "risk_label_code", "current_L1_x10", "current_L2_x10",
    "current_L3_x10", "surface_temp_x10", "ambient_temp_x10", "humidity_x10",
    "pd_magnitude_x10", "pd_pulses_x10", "arc_trip", "arc_system_state",
    "arc_link_ok", "alarm_active", "timestamp_hi", "timestamp_lo",
]

LABELS = {0: "normal", 1: "izlemede", 2: "uyarı", 3: "kritik"}


def main():
    cabinet_no = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    base = BASE_ADDRESS + (cabinet_no - 1) * REGS_PER_CABINET

    client = ModbusTcpClient("127.0.0.1", port=5020)
    if not client.connect():
        print("Modbus sunucusuna bağlanılamadı — backend çalışıyor mu?")
        return

    rr = client.read_holding_registers(base, count=len(FIELDS), slave=1)
    if rr.isError():
        print("Modbus okuma hatası:", rr)
        return

    print(f"AG-{cabinet_no:03d} (base address {base}):")
    values = dict(zip(FIELDS, rr.registers))
    print(f"  risk_score   : {values['risk_score_x10'] / 10:.1f}  ({LABELS.get(values['risk_label_code'])})")
    print(f"  current L1/L2/L3 : {values['current_L1_x10']/10:.1f} / {values['current_L2_x10']/10:.1f} / {values['current_L3_x10']/10:.1f} A")
    print(f"  surface_temp : {values['surface_temp_x10'] / 10:.1f} °C")
    print(f"  humidity     : {values['humidity_x10'] / 10:.1f} %RH")
    print(f"  pd_magnitude : {values['pd_magnitude_x10'] / 10:.1f} pC")
    print(f"  arc_trip     : {'EVET' if values['arc_trip'] else 'hayır'}")
    print(f"  alarm_active : {'EVET' if values['alarm_active'] else 'hayır'}")

    client.close()


if __name__ == "__main__":
    main()
