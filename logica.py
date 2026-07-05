import os
import psycopg2
from decimal import Decimal, InvalidOperation

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurada en el servidor")
    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.OperationalError as e:
        raise RuntimeError(f"No se pudo conectar a la base de datos: {e}")

def init_db():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                usuario_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                precio NUMERIC(10,2) NOT NULL CHECK (precio > 0),
                costo NUMERIC(10,2) NOT NULL CHECK (costo >= 0),
                cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (usuario_id, nombre)
            )
        """)
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        raise RuntimeError(f"Error al crear tabla: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def cargar_productos(usuario_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT nombre, precio, (precio - costo) as ganancia, cantidad FROM productos WHERE usuario_id = %s ORDER BY id DESC',
            (usuario_id,)
        )
        productos = []
        for p in cursor.fetchall():
            productos.append({
                'nombre': p[0],
                'precio': float(p[1]),
                'ganancia': float(p[2]),
                'cantidad': p[3]
            })
        return productos
    except Exception as e:
        print(f"Error al cargar productos: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def registrar_producto(usuario_id, nombre, precio, costo, cantidad):
    nombre = nombre.strip()
    try:
        precio = Decimal(str(precio))
        costo = Decimal(str(costo))
        cantidad = int(cantidad)
    except (ValueError, TypeError, InvalidOperation):
        return False, "Valores numéricos inválidos"

    if not nombre or len(nombre) > 50:
        return False, "El nombre no puede estar vacío ni pasar de 50 caracteres"
    if precio <= 0:
        return False, "El precio debe ser mayor a 0"
    if costo < 0:
        return False, " ❌ El costo no puede ser negativo"
    if costo > precio:
        return False, " ❌ El costo no puede ser mayor al precio"
    if cantidad <= 0:
        return False, "📦 La cantidad debe ser mayor a 0"

    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
    'INSERT INTO productos (usuario_id, nombre, precio, costo, cantidad) VALUES (%s, %s, %s, %s, %s)',
    (usuario_id, nombre, precio, costo, cantidad)
)
        conn.commit()
        return True, " ✅ 📦 Producto registrado correctamente"
    except psycopg2.IntegrityError:
        if conn: conn.rollback()
        return False, " ❌Ya tienes un producto registrado con ese nombre ❌"
    except Exception as e:
        if conn: conn.rollback()
        return False, f"⚠️Error al guardar: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def buscar_producto(usuario_id, nombre):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT nombre, precio, costo, cantidad FROM productos WHERE usuario_id = %s AND nombre = %s',
            (usuario_id, nombre)
        )
        p = cursor.fetchone()
        if p:
            return {
                'nombre': p[0],
                'precio': float(p[1]),
                'costo': float(p[2]),
                'cantidad': p[3]
            }
        return None
    except Exception as e:
        print(f"Error al buscar: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
