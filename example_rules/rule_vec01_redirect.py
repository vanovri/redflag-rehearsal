"""Example rule VEC-01: off-platform redirect (WA/Telegram)."""
import re

THRESHOLD = 0.55
CONTACT_RE = re.compile(r"(?:08\d{6,12}|\+62\s?\d{6,14}|62\d{8,13}|@[a-z0-9_.]{3,}|t\.me/\S+|wa\.me/\S+|telegram)")
INVITE_RE = re.compile(r"(lanjut|chat|hubungi|kontak|pindah|klik|order)\s+(ke\s+)?(wa|whatsapp|telegram|tele|ig|instagram|line)?")

def evaluate_rf_vec01_redirect(message):
    norm = normalize_text(message[:2000])
    score = 0.0
    fired = []
    m1 = CONTACT_RE.search(norm)
    if m1:
        score += 0.40
        fired.append("contact")
    m2 = INVITE_RE.search(norm)
    if m2:
        score += 0.30
        fired.append("offplatform-invite")
    if ("diluar" in norm or "di luar" in norm) and "aplikasi" in norm:
        score += 0.20
        fired.append("outside-app")
    score = min(1.0, score)
    flagged = score >= THRESHOLD
    tier = "HIGH" if score >= 0.8 else ("MEDIUM" if score >= 0.55 else "LOW")
    ev = []
    if m1:
        ev.append(m1.group(0)[:24])
    if m2:
        ev.append(m2.group(0)[:24])
    return RuleResult("rf_vec01_redirect", flagged, score, ev,
                      "%s: %s" % (tier, "+".join(fired) if fired else "none"))

RULE_TESTS = {
    "positive": [
        "lanjut ke WA ya kak 0812 3456 7890",
        "chat telegram saya @toko_murah99 biar cepat",
        "pindah ke wa aja, nomor 081234567890",
        "hubungi ig kami @promo.gacor biar dapat diskon",
        "klik wa.me/6281234567890 untuk order cepat",
        "lanjut di luar aplikasi ya, ke telegram 0812 tiga empat lima",
    ],
    "negative": [
        "kak barang ready ya, silakan checkout via aplikasi",
        "nomor resi sudah saya kirim via chat ini",
        "toko kami buka jam 9 pagi sampai jam 9 malam",
        "silakan komplain lewat pusat bantuan resmi",
        "stok warna hijau masih tersedia kak",
        "terima kasih sudah belanja di toko kami",
    ],
}
