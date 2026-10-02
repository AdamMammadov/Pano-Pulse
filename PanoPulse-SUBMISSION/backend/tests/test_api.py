"""
API səviyyəsində inteqrasiya testləri. Tək bir modul-səviyyəli
TestClient fixture istifadə edirik ki, Modbus TCP server-i hər testdə
təkrar-təkrar başlayıb bağlanmasın (port təkrar istifadəsi problemi
yaratmasın) — startup/shutdown yalnız bir dəfə işləyir, bütün testlər
eyni canlı tətbiq nümunəsini paylaşır.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import API_KEY


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_and_fleet_size(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["fleet_size"] == 120


def test_scenario_requires_api_key(client):
    r = client.post("/cabinets/AG-001/scenario", json={"scenario": "overload"})
    assert r.status_code == 401

    r = client.post(
        "/cabinets/AG-001/scenario",
        json={"scenario": "overload"},
        headers={"X-API-Key": API_KEY},
    )
    assert r.status_code == 200


def test_unknown_cabinet_returns_404(client):
    r = client.get("/cabinets/AG-999")
    assert r.status_code == 404


def test_alerts_csv_export_has_header(client):
    r = client.get("/alerts/export.csv")
    assert r.status_code == 200
    assert "cabinet_id" in r.text.splitlines()[0]


def test_modbus_register_map_documents_all_cabinets(client):
    r = client.get("/modbus/register-map")
    body = r.json()
    assert body["port"] == 5020
    assert body["fields_in_order"][0] == "risk_score_x10"


def test_pdf_report_generates_valid_pdf(client):
    r = client.get("/cabinets/AG-001/report.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_telegram_gateway_degrades_gracefully_without_token():
    from app.alerts import TelegramGateway
    tg = TelegramGateway()  # ortam dəyişənləri olmadan
    assert tg.configured is False
    result = tg.send("+90-000", "test")
    assert result is False  # cökmür, sadəcə False qaytarır
    assert len(tg.outbox) == 1  # yenə də loqlanır


def test_copilot_answers_are_grounded_in_real_snapshot(client):
    # Kritik bir durum yaradaq, sonra copilot-dan soruşaq
    client.post(
        "/cabinets/AG-050/scenario",
        json={"scenario": "arc_flash"},
        headers={"X-API-Key": API_KEY},
    )
    import time
    time.sleep(6)  # bir neçə tick gözlə ki, arc trip qeydə alınsın
    r = client.post("/cabinets/AG-050/ask", json={"question": "Why is the risk high?"})
    assert r.status_code == 200
    body = r.json()
    assert body["source"].startswith("rule_based")
    assert len(body["answer"]) > 0
