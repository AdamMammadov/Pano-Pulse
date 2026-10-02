"""
PanoPulse — PDF incident report
------------------------------------
Generates an automatic, field-team-ready one-page PDF incident report
for critical/warning alerts. Fully local (reportlab) — no external
service is called, consistent with the on-prem requirement.
"""
from __future__ import annotations
import io
from pathlib import Path
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Bundled DejaVu Sans — the default Helvetica/Base-14 fonts don't
# render Turkish/Azerbaijani characters (ı, ş, ğ, ü, ö, ç) correctly
# (they show as solid boxes). DejaVu has full Unicode coverage and is
# bundled with the project, so it doesn't depend on fonts installed
# on the user's own system.
_FONTS_DIR = Path(__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("DejaVu", str(_FONTS_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_FONTS_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(_FONTS_DIR / "DejaVuSans-Oblique.ttf")))


RISK_COLOR_HEX = {
    "normal": "#3FB89C",
    "watch": "#D9B23F",
    "warning": "#E3873A",
    "critical": "#E2574A",
}


def generate_incident_report(snapshot: dict) -> bytes:
    """Generates a one-page PDF incident report from a given cabinet
    snapshot. Synchronous and fast (no network call), so it can be
    called directly both from the API endpoint and when an alert fires."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - margin

    color = HexColor(RISK_COLOR_HEX.get(snapshot["risk_label"], "#888888"))

    # Header
    c.setFillColor(HexColor("#0D1214"))
    c.rect(0, height - 30 * mm, width, 30 * mm, fill=True, stroke=False)
    c.setFillColor(HexColor("#D98B3F"))
    c.setFont("DejaVu-Bold", 18)
    c.drawString(margin, height - 15 * mm, "PanoPulse — Incident Report")
    c.setFillColor(HexColor("#8B9598"))
    c.setFont("DejaVu", 10)
    c.drawString(margin, height - 22 * mm, "In-cabinet anomaly early-warning system · on-prem")
    y = height - 40 * mm

    # Cabinet identity + risk
    c.setFillColor(HexColor("#000000"))
    c.setFont("DejaVu-Bold", 14)
    c.drawString(margin, y, f"Cabinet: {snapshot['cabinet_id']}")
    c.setFillColor(color)
    c.setFont("DejaVu-Bold", 14)
    c.drawRightString(width - margin, y, f"{snapshot['risk_score']:.0f}/100 — {snapshot['risk_label'].upper()}")
    y -= 8 * mm

    c.setFillColor(HexColor("#444444"))
    c.setFont("DejaVu", 9)
    ts = snapshot.get("timestamp")
    ts_str = ts if isinstance(ts, str) else str(ts)
    c.drawString(margin, y, f"Timestamp: {ts_str}    ·    Report generated: {datetime.now(timezone.utc).isoformat()}")
    y -= 10 * mm

    # Likely cause
    if snapshot.get("likely_cause"):
        c.setFont("DejaVu-Bold", 11)
        c.drawString(margin, y, "Likely Cause:")
        y -= 6 * mm
        c.setFont("DejaVu", 10)
        c.drawString(margin, y, snapshot["likely_cause"])
        y -= 10 * mm

    # Root cause breakdown
    ranking = snapshot.get("root_cause_ranking") or []
    if ranking:
        c.setFont("DejaVu-Bold", 11)
        c.drawString(margin, y, "Root Cause Probability Breakdown:")
        y -= 6 * mm
        c.setFont("DejaVu", 10)
        for r in ranking:
            c.drawString(margin + 4 * mm, y, f"• {r['cause']} — {r['probability_pct']:.0f}%")
            y -= 5.5 * mm
        y -= 4 * mm

    # Predictive maintenance
    if snapshot.get("forecast"):
        c.setFont("DejaVu-Bold", 11)
        c.drawString(margin, y, "Predictive Maintenance:")
        y -= 6 * mm
        c.setFont("DejaVu", 10)
        c.drawString(margin, y, snapshot["forecast"]["message"])
        y -= 10 * mm

    # Sensor readings
    c.setFont("DejaVu-Bold", 11)
    c.drawString(margin, y, "Sensor Readings:")
    y -= 6 * mm
    c.setFont("DejaVu", 10)
    cur = snapshot["current"]
    rows = [
        f"Current L1/L2/L3: {cur['L1']['primary_A']} / {cur['L2']['primary_A']} / {cur['L3']['primary_A']} A",
        f"Surface temperature: {snapshot['surface_temp_C']} °C",
        f"Ambient temperature: {snapshot['ambient_temp_C']} °C",
        f"Humidity: {snapshot['humidity_pct']} %RH",
        f"Partial discharge: {snapshot['pd_magnitude_pC']} pC",
        f"ARC status: {'TRIPPED' if snapshot['arc_trip'] else 'Normal'}",
    ]
    for row in rows:
        c.drawString(margin + 4 * mm, y, row)
        y -= 5.5 * mm
    y -= 4 * mm

    # Divider line
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.line(margin, y, width - margin, y)
    y -= 8 * mm

    # Equipment & reference standards (VERIFIED, real facts only — this
    # is NOT a certification claim, only a reference to the equipment's
    # own manufacturer-stated specifications)
    c.setFont("DejaVu-Bold", 11)
    c.drawString(margin, y, "Equipment & Reference Standards:")
    y -= 6 * mm
    c.setFont("DejaVu", 9)
    equip_rows = [
        "• Cabinet enclosure: TEDAS-MLZ/2003-06.B (LV Distribution Panel Technical Specification)",
        "• ARC detection: ABB TVOC-2 Arc Guard System — manufacturer-stated: SIL-2, <1ms response time",
        "• Current measurement: MPR-53CS analyzer, Modbus RTU/TCP (register 6/8/10)",
        "• Partial discharge: Techimp HFCT-class inductive sensor",
    ]
    for row in equip_rows:
        c.drawString(margin + 4 * mm, y, row)
        y -= 5 * mm
    y -= 3 * mm
    c.setFont("DejaVu-Oblique", 8)
    c.setFillColor(HexColor("#888888"))
    c.drawString(margin, y, "Note: this list references the equipment's own manufacturer specifications; it does not constitute an independent certification claim.")
    y -= 10 * mm

    # Footer
    c.setFillColor(HexColor("#999999"))
    c.setFont("DejaVu-Oblique", 8)
    c.drawString(margin, 15 * mm, "This report was generated automatically by PanoPulse. Field verification is required.")
    c.drawRightString(width - margin, 15 * mm, f"Report ID: {snapshot['cabinet_id']}-{int(datetime.now(timezone.utc).timestamp())}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
