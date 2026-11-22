"""API de MiTienda: una tienda online sencilla.

Endpoints:
  GET  /api/salud        -> estado de la API y de sus dependencias (para healthchecks y sondas)
  GET  /api/info         -> versión y nombre del contenedor que responde (para ver el balanceo)
  GET  /api/productos    -> catálogo con el stock disponible (PostgreSQL)
  POST /api/comprar/<id> -> compra una unidad del producto <id> (resta stock)
  GET  /api/visitas      -> contador de visitas (Redis)

Configuración por variables de entorno (nunca dentro de la imagen):
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD  (o DB_PASSWORD_FILE)
  REDIS_HOST, REDIS_PORT, APP_VERSION
"""
import os
import socket

import psycopg
import redis
from flask import Flask, jsonify

app = Flask(__name__)


def secreto(nombre, defecto=""):
    """Lee un valor de NOMBRE o, si existe, del fichero indicado en NOMBRE_FILE (secretos de Docker/K8s)."""
    fichero = os.environ.get(f"{nombre}_FILE")
    if fichero and os.path.exists(fichero):
        with open(fichero, encoding="utf-8") as f:
            return f.read().strip()
    return os.environ.get(nombre, defecto)


def conexion_db():
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "mitienda"),
        user=os.environ.get("DB_USER", "tienda"),
        password=secreto("DB_PASSWORD"),
        connect_timeout=3,
    )


cache = redis.Redis(
    host=os.environ.get("REDIS_HOST", "cache"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    socket_connect_timeout=2,
)


@app.get("/api/salud")
def salud():
    estado = {"api": "ok"}
    try:
        with conexion_db() as c:
            c.execute("SELECT 1")
        estado["db"] = "ok"
    except Exception as e:  # noqa: BLE001
        estado["db"] = f"error: {e.__class__.__name__}"
    try:
        cache.ping()
        estado["cache"] = "ok"
    except Exception as e:  # noqa: BLE001
        estado["cache"] = f"error: {e.__class__.__name__}"
    codigo = 200 if estado["db"] == "ok" else 503
    return jsonify(estado), codigo


@app.get("/api/info")
def info():
    return jsonify(
        version=os.environ.get("APP_VERSION", "1.0.0"),
        contenedor=socket.gethostname(),
    )


@app.get("/api/productos")
def productos():
    with conexion_db() as c:
        filas = c.execute(
            "SELECT id, nombre, categoria, precio, stock FROM producto ORDER BY id"
        ).fetchall()
    return jsonify(
        [
            {
                "id": f[0],
                "nombre": f[1],
                "categoria": f[2],
                "precio": float(f[3]),
                "stock": f[4],
            }
            for f in filas
        ]
    )


@app.post("/api/comprar/<int:id_producto>")
def comprar(id_producto):
    with conexion_db() as c:
        fila = c.execute(
            "UPDATE producto SET stock = stock - 1 "
            "WHERE id = %s AND stock > 0 RETURNING stock",
            (id_producto,),
        ).fetchone()
    if fila is None:
        return jsonify(error="Producto inexistente o sin stock"), 409
    return jsonify(producto=id_producto, stock=fila[0])


@app.get("/api/visitas")
def visitas():
    try:
        n = cache.incr("visitas")
    except redis.RedisError:
        return jsonify(error="Caché no disponible"), 503
    return jsonify(visitas=n, contenedor=socket.gethostname())


if __name__ == "__main__":
    # Solo para pruebas locales: en el contenedor se usa gunicorn
    app.run(host="0.0.0.0", port=8000)
