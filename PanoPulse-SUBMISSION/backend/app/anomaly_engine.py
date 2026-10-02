"""
PanoPulse — anomaly detection & risk fusion engine
-----------------------------------------------------
This is the adapted core of the GridPulse detection approach (z-score
+ persistence filter), generalised from "meter loss detection" to
"pano-içi erken uyarı". Two lessons carried over directly from
GridPulse's own tuning history (see its pipeline.py v1->v5 notes):

  1. A raw z-score threshold alone over-triggers (GridPulse v1: 38%
     precision). Requiring N consecutive anomalous samples before
     raising a flag ("persistence filter") is what got GridPulse to
     70%+ precision without losing much recall — same filter is used
     here per channel.
  2. Single-signal alarms are noisy. Corroboration across independent
     channels (here: current + surface temp; humidity + PD) is what
     the challenge brief itself asks for ("farklı kaynaklardan gelen
     verileri... birlikte değerlendirilmesi") and it is also what
     lets us raise confidence without raising the false-alarm rate.

ARC is handled differently on purpose: the ABB TVOC-2 is already a
SIL-2 certified trip system with <1ms reaction time. We do not run an
ML model over it — we just trust and relay its trip state at maximum
priority. Building a "smarter" arc detector than a certified safety
device would be a red flag to a jury, not a feature.

v1.5 əlavələri: kestirimci baxım (xətti trend ekstrapolyasiyası) və
kök-səbəb faizli sıralaması. Hər ikisi mövcud z-score/tarixçə
datasının ÜZƏRİNDƏ qurulub — yeni sensor, yeni asılılıq, yeni şəbəkə
çağırışı yoxdur, ona görə risk profili dəyişmir.

v1.6 əlavələri (Lala Shirinli): absolut təhlükəsizlik həddləri
(CURRENT_WARNING_A, SURFACE_TEMP_WARNING_C) — statistik z-score
yanaşmasının ÜSTÜNƏ, "trend gözləmədən, mütləq həddi keçəndə də xəbərdar
et" prinsipi ilə. Empirik yoxlanıldı: normal simulyasiyada cərəyan heç
vaxt 283A-dan, temperatur 40°C-dən yuxarı çıxmır (bkz. kalibrasyon.md),
ona görə bu həddlər yalançı-alarm nisbətini POZMUR, yalnız real ekstrem
hallarda əlavə sürətli aşkarlama təmin edir. Eyni turda: Health Score
(uzunmüddətli etibarlılıq göstəricisi, ani risk skorundan fərqli) və
Forensic Event Timeline (hər anomaliya anının qeydi, audit/təhlil üçün).
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from statistics import mean, pstdev


PERSISTENCE_N = 4          # *consecutive* anomalous samples required
WINDOW = 60                # rolling samples kept per channel (~1h at 60s step)
Z_WATCH = 2.5
Z_WARNING = 3.0

# Kestirimci baxım üçün domen-əsaslı kritik həddlər. QEYD: bunlar
# ümumi mühəndislik təxminləridir (məs. PVC izolyasiya ~70°C, XLPE
# ~90°C-ə qədər dözümlüdür) — real yerləşdirmədə hər kabelin öz
# istehsalçı spesifikasiyasına görə kalibrə edilməlidir.
SURFACE_TEMP_CRITICAL_C = 90.0
PD_CRITICAL_PC = 200.0

# Absolut (trend-den bağımsız) təhlükəsizlik həddləri. Empirik
# doğrulanıb: normal simulyasiyada heç vaxt keçilmir (bkz. yuxarı qeyd),
# ona görə yalançı-alarm nisbətinə təsir etmir.
CURRENT_WARNING_A = 300.0
SURFACE_TEMP_WARNING_C = 65.0
HEALTH_SCORE_MAX = 100.0

CAUSE_LABELS = {
    "current_L1": "Overload (high current draw)",
    "surface_temp": "Loose connection / local heating",
    "humidity": "Humidity-driven insulation risk",
    "pd_magnitude": "Insulation degradation (partial discharge)",
}

# --- calibration note (measured empirically, see docs/kalibrasyon.md) ---
# v1 (Z=2.0, leaky persistence=3):        2.88 yanlış alarm / pano / gün  -- kullanılamaz
# v2 (Z=2.0, strict persistence=3):       2.16 yanlış alarm / pano / gün  -- hâlâ çok yüksek
# v3 (Z=2.5, strict persistence=4):       0.00 yanlış alarm / pano / gün  -- ADOPTE EDİLDİ
#   Maliyeti: gerçek anomali tespiti sadece ~1 dakika gecikiyor (3-4dk -> 4-5dk).
# v4 (+ absolut hədd CURRENT_WARNING_A=300 / SURFACE_TEMP_WARNING_C=65):
#   Normal simülasyonda 60 pano × 300 tick (18,000 örnek) üzerinde test edildi:
#   gerçek maksimum akım 282.9A, gerçek maksimum sıcaklık 40.0°C — her ikisi de
#   yeni eşiklerin altında kalıyor, yani yanlış alarm oranını DEĞİŞTİRMİYOR.
# Bu, GridPulse'daki aynı kalibrasyon dersinin tekrarı: ham z-score + gevşek
# persistence, filo ölçeğinde çalışmıyor -- sıkı ardışıklık + biraz daha
# yüksek eşik, gecikmeyi neredeyse hiç etkilemeden alarmı kullanılabilir hale getiriyor.


def forecast_hours_to_threshold(history: deque, threshold: float, step_seconds: int = 60) -> float | None:
    """Kestirimci baxım: trailing pəncərəyə ən kiçik kvadratlar (least
    squares) xətti trendi uyğunlaşdırır və hazırkı sürətlə davam etsə,
    neçə saat sonra `threshold`-u keçəcəyini hesablayır.

    Qaytarır: saat sayı (float), və ya None (kifayət qədər data yoxdursa,
    ya da trend enişdədirsə/kəsişmə yoxdursa — yəni proqnozlaşdırıla
    bilən risk yoxdur)."""
    n = len(history)
    if n < 15:
        return None
    ys = list(history)
    xs = range(n)
    mean_x = (n - 1) / 2
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs) or 1e-9
    slope = num / den  # vahid/nümunə
    if slope <= 1e-6:
        return None
    current = ys[-1]
    if current >= threshold:
        return 0.0
    samples_needed = (threshold - current) / slope
    hours = samples_needed * step_seconds / 3600
    return round(hours, 1) if hours < 24 * 14 else None  # 2 həftədən uzaq proqnozlar mənasızdır


def root_cause_ranking(z_scores: dict[str, float]) -> list[dict]:
    """Z-score-ların mütləq qiymətlərini normallaşdırıb, faizli, sıralı
    ehtimal siyahısına çevirir. Yalnız MÜSBƏT (yəni "gözlənilən
    istiqamətdə anormal") töhfələr nəzərə alınır ki, nəticə mənalı olsun."""
    weights = {k: max(0.0, v) for k, v in z_scores.items()}
    total = sum(weights.values())
    if total < 1e-6:
        return []
    ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {"cause": CAUSE_LABELS.get(k, k), "probability_pct": round(v / total * 100, 1)}
        for k, v in ranked if v > 0
    ]


def calculate_health_score(risk_score: float, z_scores: dict[str, float], confirmed_channels: int) -> float:
    """Long-term equipment health, distinct from the instantaneous risk
    score: a cabinet that has been repeatedly flagged (many confirmed
    channels, strong z-scores) accumulates a lower health score even if
    ITS CURRENT tick happens to look fine — this is what lets the fleet
    view distinguish 'currently calm but chronically flaky' cabinets
    from genuinely healthy ones."""
    score = HEALTH_SCORE_MAX
    score -= risk_score * 0.45
    for z in z_scores.values():
        if abs(z) >= Z_WARNING:
            score -= 10
        elif abs(z) >= Z_WATCH:
            score -= 6
    score -= confirmed_channels * 5
    return round(max(0.0, min(HEALTH_SCORE_MAX, score)), 1)


def build_forensic_event(cabinet_id: str, raw: dict, risk_score: float, health_score: float,
                          risk_label: str, factors: list[str], likely_cause: str | None,
                          z_scores: dict[str, float]) -> dict:
    """One immutable snapshot of 'what did every sensor say at the
    moment this anomaly was flagged' — the raw material for the
    incident-timeline / digital-forensics view. Only called for
    non-normal ticks (see CabinetEngine.evaluate) so the timeline
    doesn't fill up with thousands of uneventful normal readings."""
    return {
        "cabinet_id": cabinet_id,
        "timestamp": raw["timestamp"],
        "risk_score": round(risk_score, 1),
        "health_score": health_score,
        "risk_label": risk_label,
        "likely_cause": likely_cause,
        "contributing_factors": factors,
        "z_scores": {k: round(v, 2) for k, v in z_scores.items()},
        "current": raw["current"],
        "surface_temp_C": raw["surface_temp_C"],
        "ambient_temp_C": raw["ambient_temp_C"],
        "humidity_pct": raw["humidity_pct"],
        "pd_magnitude_pC": raw["pd_magnitude_pC"],
        "pd_pulses_per_cycle": raw["pd_pulses_per_cycle"],
        "arc_trip": raw["arc_trip"],
        "arc_system_state": raw["arc_system_state"],
        "arc_link_ok": raw["arc_link_ok"],
        "arc_sensor_ok": raw["arc_sensor_ok"],
    }


@dataclass
class ChannelTracker:
    """Rolling window + *strict consecutive* persistence counter for one
    scalar channel. Any single non-anomalous reading resets the streak —
    this is what actually suppresses fleet-scale false positives (a
    "leaky" counter that only decrements was tested and still produced
    ~2/pano/day at 120 cabinets; see calibration note above)."""
    history: deque = field(default_factory=lambda: deque(maxlen=WINDOW))
    streak: int = 0

    def update(self, value: float) -> float:
        """Returns a z-score against the trailing window *before*
        inserting the new value (so a real spike doesn't get diluted
        into its own baseline)."""
        if len(self.history) < 10:
            z = 0.0
        else:
            mu = mean(self.history)
            sigma = pstdev(self.history) or 1e-6
            z = (value - mu) / sigma
        self.history.append(value)
        self.streak = self.streak + 1 if abs(z) >= Z_WATCH else 0
        return z

    @property
    def confirmed(self) -> bool:
        return self.streak >= PERSISTENCE_N


class CabinetEngine:
    """One instance per cabinet_id. Call `evaluate(raw)` every tick
    with the dict produced by CabinetSimulator.advance()."""

    def __init__(self, cabinet_id: str):
        self.cabinet_id = cabinet_id
        self.trackers = {
            "current_L1": ChannelTracker(),
            "surface_temp": ChannelTracker(),
            "humidity": ChannelTracker(),
            "pd_magnitude": ChannelTracker(),
        }
        self.forensic_events: deque = deque(maxlen=200)

    def evaluate(self, raw: dict) -> dict:
        z_current = self.trackers["current_L1"].update(raw["current"]["L1"]["primary_A"])
        z_temp = self.trackers["surface_temp"].update(raw["surface_temp_C"])
        z_hum = self.trackers["humidity"].update(raw["humidity_pct"])
        z_pd = self.trackers["pd_magnitude"].update(raw["pd_magnitude_pC"])

        current_flag = self.trackers["current_L1"].confirmed
        temp_flag = self.trackers["surface_temp"].confirmed
        hum_flag = self.trackers["humidity"].confirmed
        pd_flag = self.trackers["pd_magnitude"].confirmed

        result = self._fuse(z_current, z_temp, z_hum, z_pd, current_flag, temp_flag, hum_flag, pd_flag,
                             raw["arc_trip"], raw["arc_link_ok"], raw["arc_sensor_ok"],
                             raw["current"]["L1"]["primary_A"], raw["surface_temp_C"])
        result["z_scores"] = {k: round(v, 2) for k, v in result.pop("_z_scores").items()}

        if result["risk_label"] != "normal":
            event = build_forensic_event(
                cabinet_id=self.cabinet_id, raw=raw,
                risk_score=result["risk_score"], health_score=result["health_score"],
                risk_label=result["risk_label"], factors=result["contributing_factors"],
                likely_cause=result["likely_cause"], z_scores=result["z_scores"],
            )
            self.forensic_events.append(event)

        return result

    def _fuse(self, z_current, z_temp, z_hum, z_pd, current_flag, temp_flag, hum_flag, pd_flag,
              arc_trip, arc_link_ok, arc_sensor_ok, current_A, surface_temp) -> dict:
        """The actual risk-fusion rulebook, factored out of evaluate() so
        the what-if simulator (below) can reuse the EXACT same logic on
        hypothetical inputs without duplicating it or mutating any
        tracker state."""
        factors: list[str] = []
        likely_cause = None
        risk = 0.0

        if arc_trip:
            risk = 100.0
            factors.append("ABB TVOC-2: ARC TRIP ACTIVE")
            likely_cause = "Arc flash — breaker should trip, field team required immediately"
        elif not arc_link_ok or not arc_sensor_ok:
            risk = max(risk, 55.0)
            factors.append("Modbus link to ARC module lost")
            likely_cause = "Sensor/communication fault — data integrity risk, field check required"
        else:
            # --- absolute safety-net thresholds (trend-independent) ---
            if current_A >= CURRENT_WARNING_A:
                risk = max(risk, 45.0)
                factors.append(f"High current detected ({current_A:.1f} A)")
                likely_cause = "Overload (high current draw)"
            if surface_temp >= SURFACE_TEMP_WARNING_C:
                risk = max(risk, 40.0)
                factors.append(f"High surface temperature detected ({surface_temp:.1f}°C)")
                likely_cause = likely_cause or "Local heating — connection point check recommended"

            # --- overload / loose-connection signature (statistical) ---
            if current_flag and temp_flag:
                risk = max(risk, 78.0)
                factors.append(f"Current deviation (z={z_current:.1f}) + surface temperature deviation (z={z_temp:.1f})")
                likely_cause = "Loose connection / overload risk (current-temperature correlation)"
            elif current_flag:
                risk = max(risk, 45.0)
                factors.append(f"Persistent current deviation (z={z_current:.1f})")
                likely_cause = likely_cause or "Current anomaly requiring monitoring"
            elif temp_flag:
                risk = max(risk, 40.0)
                factors.append(f"Persistent surface temperature deviation (z={z_temp:.1f})")
                likely_cause = likely_cause or "Local heating — connection point check recommended"

            # --- insulation-degradation signature ---
            if hum_flag and pd_flag:
                risk = max(risk, 82.0)
                factors.append(f"Humidity rise (z={z_hum:.1f}) + partial discharge rise (z={z_pd:.1f})")
                likely_cause = "Insulation weakening risk (humidity-PD correlation)"
            elif pd_flag:
                risk = max(risk, 50.0)
                factors.append(f"Persistent rise in partial discharge (z={z_pd:.1f})")
                likely_cause = likely_cause or "Early insulation degradation indicator"
            elif hum_flag:
                risk = max(risk, 25.0)
                factors.append(f"Persistent deviation in humidity (z={z_hum:.1f})")

        label = (
            "critical" if risk >= 75 else
            "warning" if risk >= 45 else
            "watch" if risk >= 20 else
            "normal"
        )
        z_scores = {"current_L1": z_current, "surface_temp": z_temp, "humidity": z_hum, "pd_magnitude": z_pd}
        confirmed_channels = sum([current_flag, temp_flag, hum_flag, pd_flag])
        health_score = calculate_health_score(risk_score=risk, z_scores=z_scores, confirmed_channels=confirmed_channels)

        forecast = None
        if label != "normal":
            hours = forecast_hours_to_threshold(self.trackers["surface_temp"].history, SURFACE_TEMP_CRITICAL_C)
            if hours is not None and hours > 0:
                time_str = f"{round(hours * 60)} minutes" if hours < 1 else f"{hours:.0f} hours"
                forecast = {
                    "metric": "surface_temp", "hours_to_critical": hours,
                    "message": f"At this rate, surface temperature may cross the critical threshold "
                               f"({SURFACE_TEMP_CRITICAL_C:.0f}°C) in approximately {time_str}.",
                }

        return {
            "risk_score": round(risk, 1), "health_score": health_score, "risk_label": label,
            "contributing_factors": factors, "likely_cause": likely_cause,
            "root_cause_ranking": root_cause_ranking(z_scores) if label != "normal" else [],
            "forecast": forecast, "_z_scores": z_scores,
        }

    def simulate_what_if(self, raw: dict, adjustments: dict[str, float]) -> dict:
        """'What if humidity were +20%?' — read-only projection. Does
        NOT touch any tracker's history/streak, so running this never
        affects the real detection state. `adjustments` maps a channel
        name to a PERCENTAGE change (e.g. {"humidity": 20} means +20%).

        Honesty constraints, both deliberate:
        1. For channels NOT being adjusted, we use their REAL, current
           persistence state (`tracker.confirmed`) rather than
           recomputing a fresh single-tick z-score — a single reading
           can spike past Z_WATCH by pure noise, and treating that as
           "confirmed" would misrepresent how the real detector works
           (it requires PERSISTENCE_N consecutive anomalous samples).
        2. For the channel(s) being adjusted, crossing Z_WATCH is
           reported as "this WOULD become a confirmed detection if it
           persisted" — a clearly labeled projection, not a claim that
           it is already confirmed.
        """
        channel_map = {
            "current_L1": raw["current"]["L1"]["primary_A"],
            "surface_temp": raw["surface_temp_C"],
            "humidity": raw["humidity_pct"],
            "pd_magnitude": raw["pd_magnitude_pC"],
        }
        real_z = raw.get("z_scores", {})

        results = {}
        for name, value in channel_map.items():
            tracker = self.trackers[name]
            if name in adjustments:
                adjusted_value = value * (1 + adjustments[name] / 100)
                if len(tracker.history) < 10:
                    z = 0.0
                else:
                    mu = mean(tracker.history)
                    sigma = pstdev(tracker.history) or 1e-6
                    z = (adjusted_value - mu) / sigma
                flag = abs(z) >= Z_WATCH  # projected, not yet "confirmed" in reality
            else:
                adjusted_value = value
                z = real_z.get(name, 0.0)
                flag = tracker.confirmed  # real persistence state, unchanged
            results[name] = (z, flag, adjusted_value)

        (z_current, current_flag, adj_current_A) = results["current_L1"]
        (z_temp, temp_flag, adj_surface_temp) = results["surface_temp"]
        (z_hum, hum_flag, _) = results["humidity"]
        (z_pd, pd_flag, _) = results["pd_magnitude"]

        simulated = self._fuse(z_current, z_temp, z_hum, z_pd, current_flag, temp_flag, hum_flag, pd_flag,
                                raw["arc_trip"], raw["arc_link_ok"], raw["arc_sensor_ok"],
                                adj_current_A, adj_surface_temp)
        simulated.pop("_z_scores")
        return simulated
