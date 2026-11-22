-- Untuk MySQL yang dipasang langsung di Windows (MySQL Installer 8.4) atau XAMPP/Laragon (MariaDB).
-- Jalankan sebagai root, contoh dari folder proyek:
--   PowerShell:  Get-Content db\init-lokal.sql | mysql -u root -p
-- Hanya untuk laptop. Di lab, user 'toko' di db-primary dibuat dengan hak terbatas (lihat buku proyek).
CREATE DATABASE IF NOT EXISTS toko CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS toko_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'toko'@'localhost' IDENTIFIED BY 'tokolokal2026';
CREATE USER IF NOT EXISTS 'toko'@'127.0.0.1' IDENTIFIED BY 'tokolokal2026';
GRANT ALL PRIVILEGES ON toko.* TO 'toko'@'localhost';
GRANT ALL PRIVILEGES ON toko.* TO 'toko'@'127.0.0.1';
GRANT ALL PRIVILEGES ON toko_test.* TO 'toko'@'localhost';
GRANT ALL PRIVILEGES ON toko_test.* TO 'toko'@'127.0.0.1';
FLUSH PRIVILEGES;
