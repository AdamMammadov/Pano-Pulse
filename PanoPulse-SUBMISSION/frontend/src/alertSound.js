// Basit bir "siren" tonu — Web Audio API ile programatik olarak
// üretilir, harici ses dosyası gerekmiyor (lisans/asset sorunu yok).
let audioCtx = null;

export function playCriticalAlertSound() {
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const now = audioCtx.currentTime;

    // İki-tonlu, kısa bir "beep-beep" — endüstriyel alarm hissi için
    [0, 0.35].forEach((offset) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(880, now + offset);
      gain.gain.setValueAtTime(0, now + offset);
      gain.gain.linearRampToValueAtTime(0.15, now + offset + 0.02);
      gain.gain.linearRampToValueAtTime(0, now + offset + 0.25);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now + offset);
      osc.stop(now + offset + 0.3);
    });
  } catch (e) {
    // Tarayıcı otomatik oynatmaya izin vermeyebilir (kullanıcı etkileşimi
    // gerektirir) — sessizce yut, dashboard yine de çalışmaya devam etsin.
  }
}
