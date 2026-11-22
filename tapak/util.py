import re

from tapak.config import CATEGORIES, SIZE_MAX, SIZE_MIN


def escape_html(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def parse_int(v, default=0):
    """Meniru parseInt(): ambil awalan bilangan bulat; selain itu `default`."""
    if isinstance(v, bool):
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v) if v == v and abs(v) != float("inf") else default
    m = re.match(r"\s*[-+]?\d+", str(v if v is not None else ""))
    return int(m.group()) if m else default


def _num(v):
    if isinstance(v, bool) or v is None or isinstance(v, (list, dict)):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f == f and f not in (float("inf"), float("-inf")) and f.is_integer() else None


def read_product(b):
    """Validasi input produk dari JSON (API admin). Mengembalikan (error, nilai)."""
    b = b if isinstance(b, dict) else {}
    name = str(b.get("name") or "").strip()
    brand = str(b.get("brand") or "").strip()
    category = str(b.get("category") or "").strip()
    price, stock = _num(b.get("price")), _num(b.get("stock"))
    if not name or len(name) > 120:
        return "nama wajib diisi (maks. 120 karakter)", None
    if len(brand) > 60:
        return "merek maks. 60 karakter", None
    if category not in CATEGORIES:
        return "kategori harus salah satu dari: " + ", ".join(CATEGORIES), None
    if price is None or price < 0 or price > 100_000_000:
        return "harga harus bilangan bulat >= 0", None
    if stock is None or stock < 0 or stock > 100_000:
        return "stok harus bilangan bulat >= 0", None
    # Rentang ukuran opsional di API (bawaan 36-46) agar klien lama tetap bekerja; bila dikirim, divalidasi.
    smin = _num(b.get("size_min")) if b.get("size_min") is not None else SIZE_MIN
    smax = _num(b.get("size_max")) if b.get("size_max") is not None else SIZE_MAX
    if smin is None or smax is None or not (SIZE_MIN <= smin <= smax <= SIZE_MAX):
        return f"ukuran harus {SIZE_MIN}-{SIZE_MAX} dan size_min <= size_max", None
    return None, {"name": name, "brand": brand, "category": category, "price": price, "stock": stock,
                  "size_min": smin, "size_max": smax}


def rupiah(n):
    return "Rp " + f"{int(n or 0):,}".replace(",", ".")
