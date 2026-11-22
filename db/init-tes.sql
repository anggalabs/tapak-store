-- Dijalankan otomatis oleh docker-compose saat volume MySQL pertama kali dibuat.
-- Basis data terpisah untuk pytest di MySQL (isinya dihapus setiap tes berjalan).
CREATE DATABASE IF NOT EXISTS toko_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON toko_test.* TO 'toko'@'%';
