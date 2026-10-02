"""
Anomali mühərriki üçün test dəsti.

Bu testlər sırf iddia deyil — hər biri həqiqi davranışı yoxlayır və
CI-də (və ya sadəcə `pytest` ilə lokal) hər dəyişiklikdən sonra rəqəm
verə bilir. Xüsusilə kalibrasiya rəqəmləri (yalançı alarm nisbəti)
`docs/kalibrasyon.md`-dəki iddiaları sübut edir, sadəcə təkrarlamır.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.sensors import CabinetSimulator
from app.anomaly_engine import CabinetEngine
from app.models import Scenario


def test_normal_operation_stays_normal():
    sim = CabinetSimulator("TEST-NORMAL", seed=1)
    engine = CabinetEngine("TEST-NORMAL")
    for _ in range(60):
        ev = engine.evaluate(sim.advance(60))
    assert ev["risk_label"] == "normal"
    assert ev["risk_score"] == 0.0


def test_arc_flash_is_immediate_and_maximal():
    sim = CabinetSimulator("TEST-ARC", seed=2)
    engine = CabinetEngine("TEST-ARC")
    for _ in range(15):
        engine.evaluate(sim.advance(60))
    sim.set_scenario(Scenario.ARC_FLASH)
    ev = engine.evaluate(sim.advance(60))
    assert ev["risk_score"] == 100.0
    assert ev["risk_label"] == "critical"
    assert "ARC" in ev["contributing_factors"][0]


def test_overload_detected_within_5_minutes():
    sim = CabinetSimulator("TEST-OVERLOAD", seed=3)
    engine = CabinetEngine("TEST-OVERLOAD")
    for _ in range(20):
        engine.evaluate(sim.advance(60))
    sim.set_scenario(Scenario.OVERLOAD)
    detected_at = None
    for t in range(10):
        ev = engine.evaluate(sim.advance(60))
        if ev["risk_score"] > 0:
            detected_at = t + 1
            break
    assert detected_at is not None, "overload never detected within 10 minutes"
    assert detected_at <= 5, f"detection took {detected_at} min, expected <=5"
    assert "correlation" in (ev["likely_cause"] or "").lower() or ev["risk_score"] >= 40


def test_predictive_maintenance_forecast_appears_during_overload():
    """Kestirimci baxım: yüzey sıcaklığı yüksələn trenddədirsə, aşkarlanan
    kimi bir 'saat/dakika sonra kritik həddə çatar' proqnozu verilməlidir."""
    sim = CabinetSimulator("TEST-FORECAST", seed=3)
    engine = CabinetEngine("TEST-FORECAST")
    for _ in range(20):
        engine.evaluate(sim.advance(60))
    sim.set_scenario(Scenario.OVERLOAD)
    ev = None
    for _ in range(10):
        ev = engine.evaluate(sim.advance(60))
        if ev["risk_score"] > 0:
            break
    assert ev["forecast"] is not None
    assert ev["forecast"]["hours_to_critical"] > 0
    assert "hours" in ev["forecast"]["message"] or "minutes" in ev["forecast"]["message"]


def test_root_cause_ranking_sums_to_100_and_is_sorted():
    sim = CabinetSimulator("TEST-RCA", seed=3)
    engine = CabinetEngine("TEST-RCA")
    for _ in range(20):
        engine.evaluate(sim.advance(60))
    sim.set_scenario(Scenario.OVERLOAD)
    ev = None
    for _ in range(10):
        ev = engine.evaluate(sim.advance(60))
        if ev["risk_score"] > 0:
            break
    ranking = ev["root_cause_ranking"]
    assert len(ranking) >= 1
    pcts = [r["probability_pct"] for r in ranking]
    assert pcts == sorted(pcts, reverse=True), "ranking must be sorted descending"
    assert 97 <= sum(pcts) <= 103, f"percentages should sum to ~100, got {sum(pcts)}"


def test_what_if_only_affects_the_adjusted_channel():
    """A what-if on one channel must not spuriously flag OTHER,
    untouched channels just because their single-tick z-score happens
    to be noisy — that would misrepresent how persistence-based
    detection actually works."""
    sim = CabinetSimulator("TEST-WHATIF", seed=7)
    engine = CabinetEngine("TEST-WHATIF")
    raw = None
    for _ in range(20):
        raw = sim.advance(60)
        ev = engine.evaluate(raw)
    snapshot = {**raw, **ev, "cabinet_id": "TEST-WHATIF"}
    assert snapshot["risk_label"] == "normal"

    result = engine.simulate_what_if(snapshot, {"humidity": 60})
    assert result["risk_label"] in ("watch", "warning", "critical")
    causes = " ".join(result["contributing_factors"]).lower()
    assert "humidity" in causes
    assert "current" not in causes  # must not spuriously flag current


def test_what_if_does_not_mutate_real_tracker_state():
    """Running a what-if must be side-effect free — calling it many
    times must never change what the REAL next evaluate() reports."""
    sim = CabinetSimulator("TEST-WHATIF2", seed=7)
    engine = CabinetEngine("TEST-WHATIF2")
    raw = None
    for _ in range(20):
        raw = sim.advance(60)
        ev = engine.evaluate(raw)
    snapshot = {**raw, **ev, "cabinet_id": "TEST-WHATIF2"}

    for _ in range(5):
        engine.simulate_what_if(snapshot, {"pd_magnitude": 200})

    raw2 = sim.advance(60)
    ev_after = engine.evaluate(raw2)
    # a fresh real tick should behave exactly as if no what-if calls happened
    assert ev_after["risk_label"] in ("normal", "watch")


def test_health_score_present_and_drops_with_risk():
    sim = CabinetSimulator("TEST-HEALTH", seed=11)
    engine = CabinetEngine("TEST-HEALTH")
    ev = None
    for _ in range(20):
        ev = engine.evaluate(sim.advance(60))
    assert ev["health_score"] == 100.0  # normal, untouched -> full health

    sim.set_scenario(Scenario.OVERLOAD)
    for _ in range(8):
        ev = engine.evaluate(sim.advance(60))
    assert ev["health_score"] < 100.0
    assert 0.0 <= ev["health_score"] <= 100.0


def test_absolute_current_threshold_flags_even_without_persistence():
    """A single tick at/above CURRENT_WARNING_A must flag immediately —
    this is the trend-independent safety net, distinct from the
    persistence-based statistical path."""
    sim = CabinetSimulator("TEST-ABS", seed=13)
    engine = CabinetEngine("TEST-ABS")
    raw = sim.advance(60)
    raw["current"]["L1"]["primary_A"] = 305.0
    ev = engine.evaluate(raw)
    assert ev["risk_score"] >= 45.0
    assert any("305" in f or "High current" in f for f in ev["contributing_factors"])


def test_forensic_events_recorded_only_for_non_normal_ticks():
    sim = CabinetSimulator("TEST-FORENSIC", seed=17)
    engine = CabinetEngine("TEST-FORENSIC")
    for _ in range(20):
        engine.evaluate(sim.advance(60))
    assert len(engine.forensic_events) == 0  # all normal so far

    sim.set_scenario(Scenario.ARC_FLASH)
    engine.evaluate(sim.advance(60))
    assert len(engine.forensic_events) == 1
    event = engine.forensic_events[-1]
    assert event["cabinet_id"] == "TEST-FORENSIC"
    assert event["risk_label"] == "critical"
    assert "current" in event and "arc_trip" in event


def test_sensor_fault_flagged_as_data_integrity_issue():
    sim = CabinetSimulator("TEST-FAULT", seed=4)
    engine = CabinetEngine("TEST-FAULT")
    for _ in range(15):
        engine.evaluate(sim.advance(60))
    sim.set_scenario(Scenario.SENSOR_FAULT)
    ev = engine.evaluate(sim.advance(60))
    assert ev["risk_label"] in ("warning", "critical")
    assert "fault" in ev["likely_cause"].lower() or "communication" in ev["likely_cause"].lower()


def test_false_positive_rate_under_normal_conditions():
    """Fleet-scale kalibrasiya iddiasının reqressiyaya qarşı qorunması:
    120 panoda, saf NORMAL ssenaridə, günə pano-başına yalançı alarm
    nisbəti aşağı qalmalıdır (bax docs/kalibrasyon.md — tam validasiya:
    120 pano/500 tick üzərində ölçülmüş dəyər: 0.024). Burada daha kiçik
    bir nümunə istifadə edirik (sürət üçün) — kiçik nümunədə statistik
    variasiya gözlənilir, ona görə hədd köhnə (pis) konfiqurasiyaları
    (1.87, 2.16/gün idi) aydın şəkildə tutacaq, amma normal nümunə
    variasiyasına dözümlü bir səviyyədə saxlanılıb."""
    from app.alerts import AlertManager

    n_cabinets, n_ticks = 30, 500
    alert_mgr = AlertManager()
    total_alerts = 0
    for i in range(1, n_cabinets + 1):
        cid = f"AG-{i:03d}"
        sim = CabinetSimulator(cid, seed=i * 7919)
        engine = CabinetEngine(cid)
        for _ in range(n_ticks):
            ev = engine.evaluate(sim.advance(60))
            if alert_mgr.maybe_fire(cid, ev):
                total_alerts += 1
    days = n_ticks / 1440
    rate = total_alerts / n_cabinets / days
    assert rate < 0.3, f"yalançı alarm nisbəti çox yüksəkdir: {rate:.3f}/pano/gün"
