"""
PanoPulse — alert manager
----------------------------
Turns risk_label transitions into alerts and fans them out to
operator-facing channels. Kept intentionally simple and on-prem:

  - dashboard : always, in-app (no external dependency)
  - sms       : via a *local* GSM modem / SIM gateway on the LAN
                (e.g. a serial/USB modem or an on-prem SMPP gateway) —
                deliberately NOT a cloud SMS API, since the brief
                requires an on-prem-only architecture (no Public Cloud)
  - whatsapp  : via WhatsApp Business On-Premise API, self-hosted on
                the same local network as the monitoring server

Both channels are implemented as a `Notifier` interface so swapping
the local GSM modem or the on-prem WhatsApp client in is a
one-file change — nothing else in the engine needs to know.
Cooldown prevents alarm fatigue: once a cabinet is in a given
severity, we don't re-fire the same severity for COOLDOWN_S.
"""
from __future__ import annotations
import os
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field


COOLDOWN_S = {"watch": 900, "warning": 300, "critical": 60}


class Notifier:
    """Base class — swap in a real on-prem GSM/WhatsApp client here."""
    channel = "base"

    def send(self, to: str, message: str) -> bool:
        raise NotImplementedError


class LocalSMSGateway(Notifier):
    """Placeholder for a local GSM-modem / SMPP gateway on the LAN.
    In the hackathon demo this just logs; on real deployment this is
    a serial-port AT-command client or an on-prem SMPP connector —
    still zero public-cloud dependency."""
    channel = "sms"

    def __init__(self):
        self.outbox: list[dict] = []

    def send(self, to: str, message: str) -> bool:
        self.outbox.append({"to": to, "message": message, "ts": time.time()})
        return True


class LocalWhatsAppGateway(Notifier):
    """Placeholder for a self-hosted WhatsApp Business On-Premise API
    client running on the same local network."""
    channel = "whatsapp"

    def __init__(self):
        self.outbox: list[dict] = []

    def send(self, to: str, message: str) -> bool:
        self.outbox.append({"to": to, "message": message, "ts": time.time()})
        return True


class TelegramGateway(Notifier):
    """Gerçek Telegram Bot API entegrasyonu (yalnızca standart kütüphane
    — ek bağımlılık yok). TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID ortam
    değişkenleri tanımlı değilse sessizce devre dışı kalır (uygulamayı
    çökertmez) — bkz. docs/guvenlik.md, "nə hələ edilməyib" mantığıyla
    aynı: eksik konfigürasyon bir hata değil, bir sonraki adımdır.

    QEYD: bu entegrasyonun gerçek https://api.telegram.org çağrısı bu
    geliştirme sandbox'ının ağ izinleri dışında olduğu için UÇTAN UCA
    test edilemedi. Kod, Telegram'ın resmi, dokümante edilmiş REST
    API'sini standart şekilde kullanıyor — kendi bot token'ınızla
    deneyin, sorun çıkarsa birlikte düzeltiriz."""
    channel = "telegram"

    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.outbox: list[dict] = []  # gönderilemeyen/test modundaki mesajlar için de log

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send(self, to: str, message: str) -> bool:
        self.outbox.append({"to": to, "message": message, "ts": time.time()})
        if not self.configured:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": self.chat_id, "text": message}).encode()
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False


@dataclass
class AlertManager:
    on_call_number: str = "+90-5xx-xxx-xxxx"     # saha ekibi — configurable per bölge
    sms: LocalSMSGateway = field(default_factory=LocalSMSGateway)
    whatsapp: LocalWhatsAppGateway = field(default_factory=LocalWhatsAppGateway)
    telegram: TelegramGateway = field(default_factory=TelegramGateway)
    _last_fired: dict[str, dict[str, float]] = field(default_factory=dict)
    log: list[dict] = field(default_factory=list)

    def maybe_fire(self, cabinet_id: str, evaluation: dict) -> dict | None:
        label = evaluation["risk_label"]
        if label == "normal":
            return None

        now = time.time()
        last = self._last_fired.setdefault(cabinet_id, {})
        if now - last.get(label, 0) < COOLDOWN_S.get(label, 300):
            return None
        last[label] = now

        cause = evaluation.get("likely_cause") or "Belirsiz anomali"
        message = f"[{label.upper()}] Cabinet {cabinet_id}: {cause}"
        if evaluation.get("forecast"):
            message += f" ({evaluation['forecast']['message']})"

        channels = ["dashboard"]
        if label in ("warning", "critical"):
            self.sms.send(self.on_call_number, message)
            channels.append("sms")
        if label == "critical":
            self.whatsapp.send(self.on_call_number, message)
            channels.append("whatsapp")
            self.telegram.send(self.on_call_number, message)
            channels.append("telegram" if self.telegram.configured else "telegram_disabled")

        alert = {
            "id": str(uuid.uuid4())[:8],
            "cabinet_id": cabinet_id,
            "severity": label,
            "message": message,
            "likely_cause": cause,
            "channels": channels,
            "timestamp": now,
            "acknowledged": False,
        }
        self.log.append(alert)
        return alert
