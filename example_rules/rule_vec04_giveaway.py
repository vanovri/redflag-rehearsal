"""Example rule VEC-04: fake giveaway / OTP fishing."""
import re

THRESHOLD = 0.55
GIVEAWAY_RE = re.compile(r"(giveaway|gifts|hadiah|menang|selamat|gratis iphone|undi berhadiah)")
OTP_RE = re.compile(r"(otp|kode verifikasi|kode otp|kirim kode|nomor hp aktif|\b\d{4,6}\b)")

def evaluate_rf_vec04_giveaway(message):
    norm = normalize_text(message[:2000])
    score = 0.0
    fired = []
    m1 = GIVEAWAY_RE.search(norm)
    if m1:
        score += 0.40
        fired.append("giveaway-lure")
    m2 = OTP_RE.search(norm)
    if m2:
        score += 0.35
        fired.append("otp-request")
    if "pajak" in norm or "biaya admin" in norm:
        score += 0.20
        fired.append("fee-ask")
    score = min(1.0, score)
    flagged = score >= THRESHOLD
    tier = "HIGH" if score >= 0.8 else ("MEDIUM" if score >= 0.55 else "LOW")
    ev = []
    if m1:
        ev.append(m1.group(0)[:24])
    if m2:
        ev.append(m2.group(0)[:24])
    return RuleResult("rf_vec04_giveaway", flagged, score, ev,
                      "%s: %s" % (tier, "+".join(fired) if fired else "none"))

RULE_TESTS = {
    "positive": [
        "selamat menang giveaway iphone, kirim kode otp",
        "hadiah gratis, balas dengan nomor hp aktif kamu",
        "undi berhadiah, kirim kode verifikasi 482913",
        "menang gifts, bayar biaya admin 50 ribu dulu",
        "gratis iphone, lunasi pajak hadiah via transfer",
        "selamat dapat hadiah, kirim kode yang masuk sms",
    ],
    "negative": [
        "promo resmi hanya diumumkan di halaman toko aplikasi",
        "kakak dapat voucher cashback otomatis saat checkout",
        "kami tidak pernah meminta kode verifikasi via chat",
        "hadiah undian resmi tanpa pungutan biaya apapun",
        "cek promo yang berlaku di banner aplikasi ya kak",
        "terima kasih sudah ikut promo toko kami",
    ],
}
