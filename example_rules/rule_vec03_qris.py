"""Example rule VEC-03: direct transfer / fake QRIS."""
import re

THRESHOLD = 0.55
TRANSFER_RE = re.compile(r"(transfer|tf langsung|bayar langsung|bayar via|bayar\b|kirim dana|qris|scan qr|rekening \d+)")
BANK_RE = re.compile(r"(bca|bri|mandiri|bni|dana|ovo|gopay|qris|qr|081\d{7,11}|\+62\d{8,13}|\b\d{10,16}\b)")

def evaluate_rf_vec03_qris(message):
    norm = normalize_text(message[:2000])
    score = 0.0
    fired = []
    m1 = TRANSFER_RE.search(norm)
    if m1:
        score += 0.40
        fired.append("transfer-intent")
    m2 = BANK_RE.search(norm)
    if m2:
        score += 0.35
        fired.append("payment-target")
    if "diskon" in norm and "langsung" in norm:
        score += 0.15
        fired.append("direct-discount")
    score = min(1.0, score)
    safe_ctx = ("aplikasi" in norm or "checkout" in norm
                or "resmi" in norm or "virtual account" in norm)
    if safe_ctx:
        score = max(0.0, score - 0.45)
        fired.append("safe-context")
    flagged = score >= THRESHOLD
    tier = "HIGH" if score >= 0.8 else ("MEDIUM" if score >= 0.55 else "LOW")
    ev = []
    if m1:
        ev.append(m1.group(0)[:24])
    if m2:
        ev.append(m2.group(0)[:24])
    return RuleResult("rf_vec03_qris", flagged, score, ev,
                      "%s: %s" % (tier, "+".join(fired) if fired else "none"))

RULE_TESTS = {
    "positive": [
        "transfer aja ke 0812 tiga empat lima enam tujuh delapan",
        "bayar langsung via qris ini biar dapat diskon",
        "kirim dana ke rekening 1234 5678 9012 ya kak",
        "scan qr ini untuk bayar langsung 500 ribu",
        "tf langsung ke dana 081234567890 biar cepat dikirim",
        "bayar via ovo 0812-3456-7890 biar cepat, skip antre",
    ],
    "negative": [
        "silakan bayar via aplikasi agar terlindungi",
        "qris resmi tersedia di halaman checkout aplikasi",
        "kakak bisa transfer via virtual account resmi",
        "pembayaran lunas akan tampil otomatis di aplikasi",
        "nomor pesanan kakak sudah tercatat di sistem",
        "diskon otomatis berlaku saat checkout di aplikasi",
    ],
}
