# TAPAK: toko sepatu untuk lab SOC (PBL RKS-313)

TAPAK adalah aplikasi web toko sepatu yang menjadi **target** di lab SOC tim RKS 3A Malam.
Pelanggan bisa melihat katalog, memesan, dan mengunggah bukti bayar. Admin mengelola produk,
pesanan, pengguna, dan laporan penjualan. Semua aktivitas penting ditulis ke log, lalu dibaca Wazuh.

> **Hanya untuk lab terisolasi.** Aplikasi punya saklar `VULN_*` yang sengaja membuka celah
> (SQL injection, IDOR, XSS, manipulasi harga, akses admin) untuk skenario serangan.
> Jangan pasang di jaringan umum dan jangan buka ke internet.

## Daftar isi
1. [Gambaran singkat](#1-gambaran-singkat)
2. [Fitur](#2-fitur)
3. [Menjalankan di laptop (uji lokal)](#3-menjalankan-di-laptop-uji-lokal)
4. [Memasang atau memperbarui di srv-web](#4-memasang-atau-memperbarui-di-srv-web)
5. [Aturan validasi form](#5-aturan-validasi-form)
6. [Log untuk Wazuh](#6-log-untuk-wazuh)
7. [Saklar kerentanan `VULN_*`](#7-saklar-kerentanan-vuln_)
8. [Struktur folder](#8-struktur-folder)
9. [Riwayat perubahan](#9-riwayat-perubahan)

---

## 1. Gambaran singkat

| Hal | Isi |
|---|---|
| Bahasa dan kerangka | Python 3, Flask (blueprint), SQLAlchemy, Flask-Migrate, WTForms, Jinja2 |
| Database | MySQL di VM `db-primary` (192.168.30.10); SQLite untuk uji lokal |
| Server | Container Docker `tapak` di VM `srv-web` (192.168.10.10), di belakang WAF ModSecurity |
| Tes otomatis | 45 tes pytest (`tests/`) |

Akun awal (kata sandi sengaja lemah untuk uji brute force):

| Username | Kata sandi | Peran |
|---|---|---|
| admin | Admin#2026 | admin |
| budi | password123 | pelanggan |
| sari | qwerty123 | pelanggan |
| andi | 123456 | pelanggan |

## 2. Fitur

**Pelanggan** (halaman web)

| Fitur | Alamat |
|---|---|
| Daftar, masuk, keluar | `/register`, `/login`, `/logout` |
| Beranda dan katalog: cari, kategori, rentang harga, halaman | `/`, `/products` |
| Detail produk: pilih ukuran yang tersedia, jumlah, ulasan | `/products/<id>` |
| Keranjang dan buat pesanan | `/cart`, `/checkout` |
| Pesanan saya dan unggah bukti bayar | `/orders`, `/orders/<id>` |

**Admin** (panel web, `/panel`)

- Setelah login, admin **langsung masuk ke dashboard panel** (`/panel/`).
- Kelola produk: tambah, ubah, hapus, foto, stok, dan **rentang ukuran** (misalnya 39-44).
- Verifikasi pembayaran: setujui atau tolak. Bila ditolak, stok dikembalikan.
- Kelola pengguna: aktifkan, nonaktifkan, hapus.
- Laporan penjualan per rentang tanggal, ekspor CSV atau Excel.

**REST API** (token Bearer, dipakai skenario serangan)

`/api/health`, `/api/register`, `/api/login`, `/api/products`, `/api/products/search`,
`/api/products/<id>/reviews`, `/api/orders`, dan API admin `/admin/stats|users|orders|products`.

**Aturan stok dan ukuran**
- Pembeli hanya bisa memilih ukuran di rentang produk itu. Toko menjual ukuran 36-46 (EU).
- Jumlah di keranjang dan di pesanan tidak boleh melebihi stok.
- Stok berkurang saat pesanan dibuat, dan kembali bila admin menolak pembayaran.

## 3. Menjalankan di laptop (uji lokal)

Diketik di **terminal di folder proyek** (PowerShell di Windows, atau terminal Linux).

```bash
pip install -r requirements-dev.txt
python -m pytest -q          # harus: 45 passed
```

Menjalankan web dengan database SQLite sementara:

```bash
# Linux / Git Bash
DATABASE_URL=sqlite:./dev.db python wsgi.py

# PowerShell
$env:DATABASE_URL="sqlite:./dev.db"; python wsgi.py
```

Buka `http://localhost:5000`. Saat pertama dijalankan, aplikasi membuat tabel, mengisi akun dan produk awal,
lalu menambahkan produk baru yang belum ada.

## 4. Memasang atau memperbarui di srv-web

### 4.1 Langkah memasang dan memperbarui

Diketik di **terminal srv-web**, sebagai pengguna dengan sudo, di folder kode `~/tapak-store`.

**a. Catat pengaturan container yang sedang berjalan.** WAF meneruskan permintaan ke container `tapak`
di jaringan Docker `tapak-net`, jadi container baru harus memakai jaringan dan alamat yang sama.

```bash
sudo docker inspect tapak --format '{{range $n, $v := .NetworkSettings.Networks}}{{$n}} {{$v.IPAddress}}{{end}} | ports={{json .HostConfig.PortBindings}} | mounts={{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}'
```

Di lab asal hasilnya seharusnya `tapak-net 172.20.0.10`. Bila berbeda, pakai nilai dari perintah ini.

**b. Siapkan `.env` dan folder** (hanya saat pemasangan pertama; saat memperbarui, `.env` lama dipakai apa adanya):

```bash
cp .env.example .env && nano .env      # isi DATABASE_URL, SECRET_KEY, VULN_*, TRUSTED_PROXIES
sudo mkdir -p /var/log/toko /var/lib/toko-uploads
```

**c. Bangun image dan jalankan ulang container:**

```bash
sudo docker build -t tapak-store .
sudo docker rm -f tapak
sudo docker run -d --name tapak --restart unless-stopped --network tapak-net --ip 172.20.0.10 \
  --env-file .env -v /var/log/toko:/srv/logs -v /var/lib/toko-uploads:/srv/uploads tapak-store
sudo docker logs tapak
```

**d. Periksa:** `sudo docker ps` menampilkan `tapak` dan `waf` berstatus Up, dan halaman toko terbuka lewat
`https://tapak.lab.local` (melalui WAF).

### 4.2 Pembaruan yang mengubah struktur database

Pembaruan November 2026 menambah dua kolom (`products.size_min`, `products.size_max`, migrasi `0003`).
Akun aplikasi `toko` biasanya tidak punya hak `ALTER`, jadi ikuti urutan ini:

1. **Cadangkan dulu.** Di terminal backup-srv: `/usr/local/bin/backup-toko.sh; echo "exit=$?"` (harus `exit=0`).
2. **Beri hak sementara.** Di terminal db-primary, di dalam `mysql` sebagai root:
   ```sql
   GRANT ALTER, CREATE, INDEX ON toko.* TO 'toko'@'192.168.10.10';
   ```
3. **Bangun ulang dan jalankan container** seperti di 4.1 langkah a, c, dan d. `.env` lama jangan ditimpa.
4. **Periksa log.** `sudo docker logs tapak` harus memuat `Running upgrade 0002 -> 0003` dan
   `produk baru ditambahkan: 12`. Pada pembaruan berikutnya angkanya `0`, artinya tidak ada yang digandakan.
5. **Cabut hak lagi.** Di db-primary:
   ```sql
   REVOKE ALTER, CREATE, INDEX ON toko.* FROM 'toko'@'192.168.10.10';
   ```

Data lama tidak diubah. Produk lama mendapat rentang ukuran 36-46, sama dengan perilaku sebelumnya.

## 5. Aturan validasi form

Validasi utama ada di **server** (`tapak/forms.py`). Validasi di browser (`tapak/static/app.js`) hanya
memberi umpan balik lebih cepat, dan **membaca aturan yang sama**. Jadi kolom wajib dan opsional cukup
ditentukan di satu tempat.

- Kolom wajib diberi tanda **\*** dan atribut HTML `required`.
- Kolom opsional diberi label **(opsional)** dan boleh dikosongkan.

| Form | Wajib | Opsional |
|---|---|---|
| Masuk | username, kata sandi | - |
| Daftar | username (3-50), email, kata sandi (min. 8, huruf dan angka), ulangi kata sandi | - |
| Produk (admin) | nama, merek, kategori, harga (0 boleh), stok (0 boleh), ukuran terkecil, ukuran terbesar (36-46, terbesar >= terkecil) | deskripsi, foto |
| Tambah ke keranjang | ukuran (dalam rentang produk), jumlah (1-10, tidak melebihi stok) | - |
| Ulasan | nilai, isi ulasan | - |
| Filter katalog | - | kata kunci, kategori, harga min, harga maks (maks >= min) |
| Laporan penjualan | - | tanggal awal, tanggal akhir (akhir >= awal) |

**Menambah kolom baru:** beri validator `InputRequired`/`DataRequired` bila wajib, atau `Optional()` bila
opsional, lalu tampilkan dengan makro `field()`. Label dan atribut `required` mengikuti otomatis.

## 6. Log untuk Wazuh

Berkas: `/var/log/toko/app.log` di srv-web. Format satu baris: `WAKTU-UTC LEVEL event=NAMA kunci=nilai`.

| Kelompok | Event |
|---|---|
| Akun | `LOGIN_OK`, `LOGIN_FAILED` (bad_password, unknown_user, inactive), `LOGOUT`, `REGISTER_OK`, `REGISTER_FAILED` |
| Admin | `ADMIN_ACCESS` (GRANTED/DENIED), `PRODUCT_CREATE`, `PRODUCT_UPDATE`, `PRODUCT_DELETE`, `USER_STATUS`, `USER_DELETE`, `REPORT_EXPORT` |
| Transaksi | `ORDER`, `ORDER_ACCESS_DENIED`, `PAYMENT_PROOF_UPLOADED`, `PAYMENT_DECISION` |
| Lain-lain | `SEARCH`, `SERVER_ERROR` |

- Nilai yang mengandung spasi atau baris baru di-escape, supaya penyerang tidak bisa memalsukan baris log.
- **IP klien:** header `X-Real-IP`/`X-Forwarded-For` hanya dipercaya bila koneksi datang dari alamat di
  `TRUSTED_PROXIES` (isi dengan alamat WAF). Tanpa itu, log memakai alamat koneksi langsung.

## 7. Saklar kerentanan `VULN_*`

Diatur di `.env`. Nilai `1` = celah dibuka, `0` = aman.

| Saklar | Bila `1` |
|---|---|
| `VULN_SQLI` | `/api/products/search` memakai SQL mentah (SQL injection) |
| `VULN_IDOR` | `/api/orders/<id>` tidak memeriksa pemilik pesanan |
| `VULN_XSS` | isi ulasan disimpan dan ditampilkan apa adanya |
| `VULN_PRICE` | harga dari klien dipercaya saat membuat pesanan lewat API |
| `VULN_ADMIN` | API admin `/admin/*` bisa diakses tanpa login |

Halaman web (`/products`, `/panel`) memakai ORM dan tidak terpengaruh `VULN_SQLI` maupun `VULN_ADMIN`.
Validasi ukuran dan stok berlaku di web dan API, apa pun nilai saklarnya.

## 8. Struktur folder

```
wsgi.py               titik masuk: migrasi, data awal, lalu jalankan web
tapak/
  __init__.py         create_app() dan init_database()
  config.py           konfigurasi dari .env, daftar kategori, batas ukuran 36-46
  models.py           tabel: User, Product, Order, OrderItem, Review
  forms.py            form dan aturan validasi (wajib/opsional)
  services.py         login, daftar, buat pesanan (cek ukuran dan stok)
  seed.py             akun dan produk awal, produk tambahan
  security.py         hash kata sandi, token API, sesi web
  logs.py             penulisan log dan IP klien
  uploads.py          validasi dan simpan gambar
  blueprints/         auth.py, shop.py, admin_web.py (web) · api.py, admin_api.py (JSON)
  templates/          halaman Jinja2
  static/             style.css, app.js (validasi di browser)
migrations/versions/  0001 skema awal · 0002 kolom fitur web · 0003 rentang ukuran produk
tests/                tes pytest
```

## 9. Riwayat perubahan

**November 2026, menindaklanjuti catatan dosen**
- Admin langsung diarahkan ke dashboard panel setelah login.
- Validasi ukuran: admin mengisi rentang ukuran tiap produk (36-46, terbesar >= terkecil). Halaman produk hanya
  menampilkan ukuran itu, dan server menolak ukuran di luar rentang, baik dari web maupun API.
- Validasi kolom wajib dan opsional diperbaiki. Sebelumnya semua kolom dianggap wajib, karena makro form menulis
  `required="None"` untuk kolom opsional. Kini kolom wajib bertanda \*, kolom opsional berlabel (opsional),
  dan pesan galat berbahasa Indonesia.
- Perbaikan bug:
  - Harga dan stok bernilai 0 sebelumnya ditolak.
  - Isian bukan angka menampilkan pesan berbahasa Inggris.
  - Pesanan bisa melebihi stok.
  - Pesan galat keranjang tidak menjelaskan penyebabnya.
- 12 produk baru, termasuk kategori baru **formal**. Total katalog 36 produk.
- Tes bertambah dari 39 menjadi 45.
