"""Titik masuk: `gunicorn wsgi:app` (Docker) atau `python wsgi.py` (uji lokal)."""
import os

from dotenv import load_dotenv

# Baca .env di folder proyek bila ada (uji lokal). Variabel yang sudah diset (misalnya dari
# `docker run --env-file`) tidak ditimpa.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from tapak import create_app, init_database  # noqa: E402

app = create_app()
print("seed selesai" if init_database(app) else "data sudah ada, seed dilewati", flush=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
