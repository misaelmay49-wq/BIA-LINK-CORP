import os
import psycopg2
from psycopg2.extras import RealDictCursor 
from decimal import Decimal 

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

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'], cursor_factory=RealDictCursor)

def obtener_productos(usuario_id):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur: 
                cur.execute("""
        INSERT INTO ventas (usuario_id, producto_id, nombre_producto, precio, costo, ganancia_unitaria, cantidad_vendida, total_venta, ganancia_total) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (usuario_id, producto_id, nombre, precio, costo, ganancia_u, cantidad_vendida, total, ganancia_t))
                productos = cur.fetchall()
        return True, "OK", productos
    except Exception as e:
        return False, str(e), []

def procesar_venta_logica(producto_id, cantidad_vendida, usuario_id):
    conn = None
    try:
        with get_db() as conn:
            with conn.cursor() as cur:  # ← with aquí también, ya consistente
                if cantidad_vendida <= 0:
                    return False, "❌ La cantidad debe ser mayor a 0"

                cur.execute("""
                    SELECT id, nombre, precio, costo, cantidad
                    FROM productos
                    WHERE id = %s AND usuario_id = %s
                    FOR UPDATE
                """, (producto_id, usuario_id))
                p = cur.fetchone()

                if not p:
                    return False, "❌ Producto inválido"

                nombre = p['nombre']
                precio = Decimal(p['precio'])
                costo = Decimal(p['costo'])
                cantidad = int(p['cantidad'])
                ganancia = precio - costo

                if cantidad_vendida > cantidad:
                    return False, f"❌ No hay suficiente stock. Disponible: {cantidad}"

                cur.execute("""
                    UPDATE productos
                    SET cantidad = cantidad - %s
                    WHERE id = %s
                """, (cantidad_vendida, producto_id))

                total_venta = precio * cantidad_vendida
                ganancia_total = ganancia * cantidad_vendida

                cur.execute("""
                    INSERT INTO ventas (producto_id, usuario_id, nombre_producto, precio,
                                        costo, ganancia_unitaria, cantidad_vendida,
                                        total_venta, ganancia_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (producto_id, usuario_id, nombre, precio, costo, ganancia,
                      cantidad_vendida, total_venta, ganancia_total))

                conn.commit()
                return True, f"✅ Venta registrada: {cantidad_vendida} x {nombre}"
                
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"❌ Error: {e}"
