"""Rentang ukuran per produk: products.size_min dan products.size_max. Idempoten.

Baris lama otomatis bernilai 36 dan 46 (server_default), sama dengan perilaku sebelumnya.
Catatan MySQL: butuh hak ALTER sementara untuk user aplikasi, sama seperti 0002 (lihat README).

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

COLUMNS = [
    sa.Column("size_min", sa.Integer, nullable=False, server_default="36"),
    sa.Column("size_max", sa.Integer, nullable=False, server_default="46"),
]


def upgrade():
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("products")}
    for col in COLUMNS:
        if col.name not in have:
            op.add_column("products", sa.Column(col.name, col.type, nullable=col.nullable, server_default=col.server_default))


def downgrade():
    with op.batch_alter_table("products") as b:
        for col in COLUMNS:
            b.drop_column(col.name)
