from tapak.extensions import db
from tapak.models import Product, User
from tapak.security import hash_password

# Kata sandi sengaja lemah untuk uji brute force (hanya lab).
USERS = [("admin", "Admin#2026", "admin"), ("budi", "password123", "client"),
         ("sari", "qwerty123", "client"), ("andi", "123456", "client")]
# Merek fiktif (bukan merek dagang nyata).
PRODUCTS = [
    ("Langkah Runner Pro", "Langkah", "lari", 549000, 40), ("Rimba Trail X", "Rimba", "gunung", 699000, 25),
    ("Bayu Street Low", "Bayu", "kasual", 399000, 60), ("Langkah Court Elite", "Langkah", "basket", 799000, 20),
    ("Bayu Classic Canvas", "Bayu", "kasual", 289000, 80), ("Rimba Hiker Mid", "Rimba", "gunung", 850000, 15),
    ("Langkah Sprint Lite", "Langkah", "lari", 459000, 35), ("Bayu Sandal Pantai", "Bayu", "sandal", 149000, 100),
    ("Kilat Aero Racer", "Kilat", "lari", 629000, 30), ("Kilat Tempo Flow", "Kilat", "lari", 749000, 22),
    ("Garuda Slam High", "Garuda", "basket", 899000, 18), ("Garuda Court Low", "Garuda", "basket", 649000, 26),
    ("Garuda Futsal Strike", "Garuda", "futsal", 479000, 45), ("Nusa Pasir Slide", "Nusa", "sandal", 179000, 90),
    ("Nusa Kampung Loafer", "Nusa", "kasual", 349000, 50), ("Nusa Batik Sneaker", "Nusa", "kasual", 429000, 40),
    ("Cakra Deck Pro", "Cakra", "skate", 559000, 28), ("Cakra Ollie Mid", "Cakra", "skate", 519000, 24),
    ("Cakra Street Vulc", "Cakra", "skate", 459000, 33), ("Ombak Aqua Trail", "Ombak", "gunung", 599000, 20),
    ("Ombak Wave Slide", "Ombak", "sandal", 199000, 70), ("Ombak Marathon Elite", "Ombak", "lari", 1199000, 12),
    ("Kilat Futsal Turbo", "Kilat", "futsal", 519000, 38), ("Bayu Retro 90", "Bayu", "kasual", 479000, 55),
]
# Produk tambahan (pembaruan November 2026), dengan rentang ukuran masing-masing:
# (nama, merek, kategori, harga, stok, ukuran terkecil, ukuran terbesar, deskripsi)
PRODUCTS_2 = [
    ("Nusa Oxford Klasik", "Nusa", "formal", 689000, 30, 38, 45, "Sepatu pantofel kulit sintetis bertali, cocok untuk kantor dan acara resmi."),
    ("Garuda Derby Kulit", "Garuda", "formal", 759000, 20, 39, 45, "Derby kulit dengan sol karet anti selip."),
    ("Bayu Loafer Kantor", "Bayu", "formal", 529000, 35, 37, 44, "Loafer tanpa tali, ringan untuk dipakai seharian."),
    ("Langkah Ultra Cushion", "Langkah", "lari", 899000, 25, 39, 46, "Bantalan tebal untuk lari jarak jauh."),
    ("Ombak Daily Jog", "Ombak", "lari", 389000, 60, 36, 45, "Sepatu lari harian dengan upper jaring yang sejuk."),
    ("Kilat Rim Rocker", "Kilat", "basket", 699000, 22, 40, 46, "Potongan tinggi untuk menjaga pergelangan kaki."),
    ("Cakra Slip-On Canvas", "Cakra", "kasual", 259000, 75, 36, 44, "Slip-on kanvas polos, mudah dipadukan."),
    ("Garuda Kanvas Tinggi", "Garuda", "kasual", 339000, 45, 36, 45, "Sneaker kanvas potongan tinggi."),
    ("Ombak Futsal Grip", "Ombak", "futsal", 449000, 40, 38, 45, "Sol karet bertekstur untuk lapangan indoor."),
    ("Bayu Skate Low", "Bayu", "skate", 399000, 30, 37, 45, "Sol vulkanisir dan ujung diperkuat untuk skateboard."),
    ("Nusa Sandal Anyam", "Nusa", "sandal", 159000, 80, 36, 44, "Sandal anyaman tali untuk santai."),
    ("Kilat Trail Runner", "Kilat", "gunung", 729000, 18, 39, 46, "Sepatu lari lintas alam dengan sol bergerigi."),
]


def seed():
    """Isi data awal bila tabel users kosong. Mengembalikan True bila data dibuat."""
    if db.session.scalars(db.select(User.id).limit(1)).first():
        return False
    for u, p, r in USERS:
        db.session.add(User(username=u, email=f"{u}@tapak.local", password_hash=hash_password(p), role=r))
    for n, br, cat, pr, st in PRODUCTS:
        db.session.add(Product(name=n, brand=br, category=cat, price=pr, stock=st))
    db.session.commit()
    return True


def sync_products():
    """Tambahkan produk PRODUCTS_2 yang belum ada (dicocokkan dari nama). Aman dijalankan berulang:
    produk yang sudah ada, termasuk yang sudah diubah admin, tidak disentuh. Mengembalikan jumlah yang ditambahkan."""
    have = set(db.session.scalars(db.select(Product.name)).all())
    added = 0
    for n, br, cat, pr, st, smin, smax, desc in PRODUCTS_2:
        if n not in have:
            db.session.add(Product(name=n, brand=br, category=cat, price=pr, stock=st, size_min=smin, size_max=smax, description=desc))
            added += 1
    db.session.commit()
    return added
