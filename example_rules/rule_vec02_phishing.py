"""Example rule VEC-02: fake refund / phishing link."""
import re

THRESHOLD = 0.55
LINK_RE = re.compile(r"(https?://\S+|bit\.ly/\S+|tinyurl\.\S+|\S+\.(xyz|top|click|link|info)\S*)")
REFUND_RE = re.compile(r"(refund|pengembalian|dana kembali|verifikasi|klik link|isi data|login)")

def evaluate_rf_vec02_phishing(message):
    norm = normalize_text(message[:2000])
    score = 0.0
    fired = []
    m1 = LINK_RE.search(norm)
    if m1:
        score += 0.40
        fired.append("suspicious-link")
    m2 = REFUND_RE.search(norm)
    if m2:
        score += 0.35
        fired.append("refund-lure")
    if "otp" in norm or "kode verifikasi" in norm:
        score += 0.20
        fired.append("otp-ask")
    score = min(1.0, score)
    flagged = score >= THRESHOLD
    tier = "HIGH" if score >= 0.8 else ("MEDIUM" if score >= 0.55 else "LOW")
    ev = []
    if m1:
        ev.append(m1.group(0)[:24])
    if m2:
        ev.append(m2.group(0)[:24])
    return RuleResult("rf_vec02_phishing", flagged, score, ev,
                      "%s: %s" % (tier, "+".join(fired) if fired else "none"))

RULE_TESTS = {
    "positive": [
        "dana refund, klik link http://toko-refund.xyz/login",
        "pengembalian dana, isi data di bit.ly/refund-cepat",
        "verifikasi akun, login di https://toko-promo.top/refund",
        "klik link ini untuk dana kembali https://tinyurl.x/abc123",
        "refund disetujui, kirim kode otp ke kami",
        "isi data rekening di link promo-info.click biar refund cair",
    ],
    "negative": [
        "refund akan diproses otomatis via aplikasi ya kak",
        "silakan ajukan pengembalian lewat menu pesanan saya",
        "dana kembali maksimal 3 hari kerja ke saldo",
        "kakak bisa cek status refund di aplikasi",
        "kami tidak pernah meminta kode otp via chat",
        "link resmi toko hanya di halaman aplikasi ini",
    ],
}
