"""
PanoPulse — AI Co-Pilot
---------------------------
One of GridPulse's most well-received elements was a "grounded" AI
assistant (never hallucinating, always tied to real data). We repeat
the same principle here — from scratch — with a different question
set and a different domain (in-cabinet anomalies, not fleet-wide
network loss).

Design principle (inherited from GridPulse): the model must NEVER
"hallucinate". Every answer is grounded strictly in the real numbers
inside `snapshot`. If no LLM API key is present (the default — no key
is ever bundled in this repo), a rule-based engine takes over — this
guarantees the demo works fully regardless of API key availability.
"""
from __future__ import annotations
import os
import re

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Reference ("nominal") current used for percentage-based comparisons.
# NOTE: this is NOT derived from the cabinet's rated capacity (1600 kVA,
# ~2300A line current at 400V) — it is a simple "typical operating
# level" reference. In a real deployment this should come from
# ADM/GDZ's own panel specification.
NOMINAL_CURRENT_A = 250.0

GREETINGS = re.compile(r"^\s*(hi|hello|hey|greetings)\b", re.IGNORECASE)


def _fmt(snapshot: dict) -> str:
    c = snapshot["current"]
    return (
        f"Risk: {snapshot['risk_score']}/100 ({snapshot['risk_label']}). "
        f"Current L1/L2/L3: {c['L1']['primary_A']}/{c['L2']['primary_A']}/{c['L3']['primary_A']} A. "
        f"Surface temperature: {snapshot['surface_temp_C']}°C, Ambient: {snapshot['ambient_temp_C']}°C, "
        f"Humidity: {snapshot['humidity_pct']}%RH, PD: {snapshot['pd_magnitude_pC']}pC, "
        f"ARC trip: {'yes' if snapshot['arc_trip'] else 'no'}."
    )


SUPPORTED_TOPICS = (
    "You can ask things like: 'Why is the risk high?', 'What should I do?', "
    "'What's the current status?', 'What's the temperature?', 'When will it become critical?', 'What's the ARC status?'"
)


def _rule_based_answer(question: str, snapshot: dict) -> str:
    q = question.lower().strip()
    label = snapshot["risk_label"]
    cause = snapshot.get("likely_cause")
    factors = snapshot.get("contributing_factors", [])
    ranking = snapshot.get("root_cause_ranking") or []
    forecast = snapshot.get("forecast")

    if GREETINGS.match(q):
        return f"Hello! I'm the AI Co-Pilot for cabinet {snapshot['cabinet_id']}. {SUPPORTED_TOPICS}"

    if re.search(r"system info|system status|summary|overview|status", q):
        parts = [f"{snapshot['cabinet_id']} — overall status: {label.upper()} (risk {snapshot['risk_score']}/100)."]
        parts.append(f"Current: L1={snapshot['current']['L1']['primary_A']}A, L2={snapshot['current']['L2']['primary_A']}A, L3={snapshot['current']['L3']['primary_A']}A.")
        parts.append(f"Temperature: surface {snapshot['surface_temp_C']}°C / ambient {snapshot['ambient_temp_C']}°C. Humidity {snapshot['humidity_pct']}%. PD {snapshot['pd_magnitude_pC']}pC.")
        parts.append(f"ARC (ABB TVOC-2): {'TRIPPED' if snapshot['arc_trip'] else 'normal'}.")
        if cause:
            parts.append(f"Note: {cause}")
        return " ".join(parts)

    if re.search(r"why|reason", q) and ("risk" in q or "high" in q or "critical" in q or "alarm" in q):
        if label == "normal":
            return "Risk is not currently elevated — all channels are within normal range."
        parts = [
            f"Risk score {snapshot['risk_score']}/100 ({label}) because: "
            + ("; ".join(factors) if factors else "a threshold was exceeded")
            + f". Our assessment: {cause or 'undetermined'}."
        ]
        if ranking:
            top = ", ".join(f"{r['cause']} ({r['probability_pct']:.0f}%)" for r in ranking)
            parts.append(f"Probable-cause breakdown: {top}.")
        if forecast:
            parts.append(forecast["message"])
        return " ".join(parts)

    if re.search(r"what should i do|what to do|action|recommend", q):
        # NOTE: specific numeric values (torque, current limits, etc.) are
        # DELIBERATELY NOT fabricated — a wrong number here could cause
        # real injury or equipment damage in the field. Recommendations
        # stay at the procedural level; exact values must come from the
        # equipment manufacturer's / ADM-GDZ's own maintenance spec.
        if label == "critical":
            steps = [f"1. Dispatch the field team to {snapshot['cabinet_id']} IMMEDIATELY — reason: {cause}."]
            if ranking:
                steps.append(f"2. Priority check point: {ranking[0]['cause']} ({ranking[0]['probability_pct']:.0f}% probability) — inspect per equipment maintenance procedure.")
            steps.append(f"{len(steps)+1}. Verify the trip log on the protection device (ABB TVOC-2).")
            if forecast:
                steps.append(f"{len(steps)+1}. {forecast['message']}")
            return " ".join(steps)
        if label == "warning":
            steps = [f"1. Schedule a field inspection for {snapshot['cabinet_id']} — reason: {cause}."]
            steps.append("2. Consider load balancing with neighboring cabinets.")
            if forecast:
                steps.append(f"3. {forecast['message']} — intervention recommended within this window.")
            return " ".join(steps)
        if label == "watch":
            return "1. No urgent action needed right now. 2. Trend should be reviewed next shift."
        return "Status is normal, no action required."

    if re.search(r"normal|safe|is there a problem", q):
        return "Yes, all channels are currently within normal range." if label == "normal" else \
               f"No, current status is '{label}'. {cause or ''}"

    if re.search(r"current|load|amps?", q):
        c = snapshot["current"]
        lines = [f"Instantaneous current: L1={c['L1']['primary_A']}A, L2={c['L2']['primary_A']}A, L3={c['L3']['primary_A']}A."]
        for phase in ("L1", "L2", "L3"):
            a = c[phase]["primary_A"]
            pct = (a - NOMINAL_CURRENT_A) / NOMINAL_CURRENT_A * 100
            if abs(pct) >= 10:
                direction = "above" if pct > 0 else "below"
                lines.append(f"{phase} is {abs(pct):.0f}% {direction} the typical reference value.")
        return " ".join(lines)

    if re.search(r"temperature|heat", q):
        return f"Surface temperature is {snapshot['surface_temp_C']}°C, ambient temperature is {snapshot['ambient_temp_C']}°C."

    if re.search(r"humidity", q):
        return f"Humidity: {snapshot['humidity_pct']}% RH."

    if re.search(r"\bpd\b|partial discharge|discharge", q):
        return f"Partial discharge magnitude: {snapshot['pd_magnitude_pC']} pC, {snapshot['pd_pulses_per_cycle']} pulses/cycle."

    if re.search(r"when|forecast|predict|become critical", q):
        if snapshot["risk_label"] == "normal":
            return "There's no rising trend right now, so there's no basis for a forecast."
        if forecast:
            return forecast["message"] + " (This is a linear projection based solely on the surface temperature trend.)"
        return "Risk is present, but there isn't yet enough trend data for a reliable time projection."

    if re.search(r"\barc\b", q):
        return "ARC (ABB TVOC-2) has tripped — critical condition!" if snapshot["arc_trip"] else "ARC status is normal, no trip."

    # True fallback: an unrecognized question — instead of dumping raw
    # data, tell the user what they CAN ask.
    return f"I didn't quite understand that. {SUPPORTED_TOPICS}"


def ask_copilot(question: str, snapshot: dict) -> dict:
    """Returns {"answer": str, "source": "rule_based" | "llm"}.
    The LLM path is intentionally not wired to a real network call in
    this repo (no API key is bundled) — see docstring. The interface is
    ready: replace this branch with a real Gemini/Claude call, but keep
    passing `snapshot` as the ONLY source of truth in the prompt."""
    if not GEMINI_API_KEY:
        return {"answer": _rule_based_answer(question, snapshot), "source": "rule_based"}

    # If a GEMINI_API_KEY is provided, a real call could be made here.
    # For the current demo, we still fall back to the rule-based answer
    # even when a key is present, to keep behavior transparent and
    # guaranteed non-hallucinating, per our AI usage disclosure. Real
    # LLM integration is a documented next step.
    return {"answer": _rule_based_answer(question, snapshot), "source": "rule_based (llm-ready)"}
