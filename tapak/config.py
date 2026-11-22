"""Konfigurasi aplikasi: semua nilai dibaca dari variabel lingkungan (.env), tidak ada rahasia di kode."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VULN_KEYS = ["VULN_SQLI", "VULN_IDOR", "VULN_XSS", "VULN_PRICE", "VULN_ADMIN"]
CATEGORIES = ["lari", "gunung", "basket", "kasual", "sandal", "futsal", "skate", "formal"]
SIZE_MIN, SIZE_MAX = 36, 46  # batas ukuran yang dijual toko (EU)
MIGRATIONS_DIR = os.path.join(ROOT, "migrations")


DB_HELP = ("DATABASE_URL wajib diisi dengan alamat MySQL, contoh: "
           "mysql://toko:SANDI@127.0.0.1:3306/toko (lihat README bagian 3). "
           "Karakter khusus di sandi harus di-URL-encode, misalnya # menjadi %23 dan @ menjadi %40.")


def normalize_db_url(url):
    """Ubah format lama (mysql://, sqlite::memory:) ke URL SQLAlchemy. Tidak ada nilai bawaan:
    bila DATABASE_URL kosong, aplikasi menolak start (lihat create_app), bukan diam-diam memakai SQLite."""
    if not url:
        return None
    if url.startswith("mysql://"):
        return "mysql+pymysql://" + url[len("mysql://"):] + ("" if "?" in url else "?charset=utf8mb4")
    if url in ("sqlite::memory:", "sqlite:memory:"):
        return "sqlite://"
    if url.startswith("sqlite:") and not url.startswith("sqlite://"):
        return "sqlite:///" + url[len("sqlite:"):]
    return url


def load_config(env=None):
    env = os.environ if env is None else env
    uri = normalize_db_url(env.get("DATABASE_URL"))
    cfg = dict(
        SECRET_KEY=env.get("SECRET_KEY") or "ganti-di-env-lab",
        SQLALCHEMY_DATABASE_URI=uri,
        VULN={k: env.get(k) == "1" for k in VULN_KEYS},
        LOG_FILE=env.get("LOG_FILE") or os.path.join(ROOT, "logs", "app.log"),
        UPLOAD_DIR=env.get("UPLOAD_DIR") or os.path.join(ROOT, "uploads"),
        MAX_CONTENT_LENGTH=3 * 1024 * 1024,
        MAX_IMAGE_BYTES=2 * 1024 * 1024,
        # Proksi tepercaya (IP/CIDR, pisah koma). Hanya dari alamat ini header X-Real-IP/X-Forwarded-For dipercaya.
        TRUSTED_PROXIES=[x.strip() for x in (env.get("TRUSTED_PROXIES") or "").split(",") if x.strip()],
        PER_PAGE=12,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=env.get("COOKIE_SECURE") == "1",
    )
    if uri and uri.startswith("mysql"):
        cfg["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 280}
    return cfg
