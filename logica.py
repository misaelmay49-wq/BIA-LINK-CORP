import os
import logging
import psycopg2
from psycopg2 import errors as pg_errors
from psycopg2.extras import RealDictCursor 
from decimal import Decimal, InvalidOperation 
from datetime import datetime
import pytz

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
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM productos WHERE usuario_id = %s", (usuario_id,)) 
                productos = cur.fetchall()
                return True, "OK", productos
    except Exception as e:
                print(f" Error obtener_productos:{e}")
                return False, str(e), []
               
def procesar_venta_logica(producto_id, cantidad_vendida, usuario_id):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                if cantidad_vendida <= 0:
                    return False, "❌ La cantidad debe ser mayor a 0"

                cur.execute("""
                    SELECT identificación, nombre, precio, costo, cantidad
                    FROM productos
                    WHERE "identificación" = %s AND usuario_id = %s
                    FOR UPDATE
                """, (producto_id, usuario_id))
                p = cur.fetchone()

                if not p:
                    return False, "❌ Producto inválido"
                    
                producto_id_db = p['identificación']
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
                    WHERE "identificación" = %s
                """, (cantidad_vendida, producto_id_db))

                total_venta = precio * cantidad_vendida
                ganancia_total = ganancia * cantidad_vendida

                cur.execute("""
                    INSERT INTO ventas (usuario_id, producto_id, nombre_producto, precio, costo, ganancia_unitaria, cantidad_vendida, total_venta, ganancia_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (usuario_id, producto_id, nombre, precio, costo, ganancia, cantidad_vendida, total_venta, ganancia_total))
                
                conn.commit()
                return True, f"✅ Venta registrada: {cantidad_vendida, producto_id_db} x {nombre}"
                
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"❌ Error: {e}" 
def analizar_ventas(usuario_id, get_conn, tz='America/Mexico_City'):
    """
    Versión corregida con columnas reales: cantidad_vendida, venta_total, ganancia_total
    """
    print("\n- GANANCIA DEL DIA -")
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
          SELECT 
            p.nombre,
            SUM(v.cantidad) AS unidades_vendidas,
            SUM(v.total) AS ganancia_bruta,
            SUM(v.ganancia) AS ganancia_neta
          FROM ventas v
          JOIN productos p ON v.producto_id = p.identificación
          WHERE v.usuario_id = %s 
          AND v.fecha >= ((NOW() AT TIME ZONE %s)::date) AT TIME ZONE 'UTC'
          AND v.fecha < ((((NOW() AT TIME ZONE %s)::date) + INTERVAL '1 day') AT TIME ZONE 'UTC')
          GROUP BY p.nombre
     """, (usuario_id, tz, tz))

        ventas = cursor.fetchall()
        
        print("[DEBUG] Fecha HOY en México:", (datetime.now(pytz.timezone(tz))).date())
        print("[DEBUG] Ventas encontradas:", len(ventas), ventas)
        print("[DEBUG] Usuario ID:", usuario_id)
        print("[DEBUG] TZ usada:", tz)
        print("[DEBUG] Fecha hoy en esa TZ:", (datetime.now(pytz.timezone(tz))).date())
        print("[DEBUG] Ventas crudas de BD:", ventas)

        if len(ventas) == 0:
            print("❌ No hay ventas registradas hoy")
            return False, {}, Decimal("0.00")

        productos = {}
        total_dia = Decimal("0.00")

        for nombre, unidades, ganancia_bruta, ganancia_neta in ventas:
            unidades = int(unidades)
            ganancia_bruta = Decimal(str(ganancia_bruta))
            ganancia_neta = Decimal(str(ganancia_neta))
            total_dia += ganancia_neta

            productos[nombre] = {
                "unidades": unidades,
                "ganancia_bruta": ganancia_bruta,
                "ganancia_neta": ganancia_neta,
                "rendimiento": "bueno" if ganancia_neta >= 500 else "bajo"
            }

        print("\n📊 RESUMEN DEL DÍA ")
        for nombre, datos in productos.items():
            print(f"{nombre} -> Ganancia Neta ${round(datos['ganancia_neta'],2)}")
            print("✅ Buen producto(se vende bien)" if datos['ganancia_neta'] >= 500 else "❌ Bajo rendimiento")

        print("\n💰 GANANCIA REAL DEL DÍA:", round(total_dia, 2))
        if total_dia >= 2000: print("🔥 Excelente dia")
        elif total_dia >= 1000: print("😊 Buen día")
        else: print("⚠️ Dia bajo")

        print("\n🔥 Sugerencias:")
        for nombre, datos in productos.items():
            if datos['ganancia_neta'] < 300: print(f"Haz promocion en {nombre}")

        return True, productos, total_dia

    except Exception as e:
        print("❌ Error al analizar ventas:", e)
        return False, {}, Decimal("0.00")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def rellenar_stock(get_conn, usuario_id, opcion, cantidad_agregar):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT "identificación", nombre, precio, costo, cantidad FROM productos WHERE usuario_id = %s ORDER BY "identificación"',
            (usuario_id,)
        )
        lineas = cursor.fetchall()

        if len(lineas) == 0:
            return False, "❌ No hay productos registrados", None
            
        productos = {}
        for i, linea in enumerate(lineas):
            identificacion = linea[0]
            nombre = linea[1]
            precio = Decimal(linea[2])
            costo = Decimal(linea[3])
            stock = int(linea[4])
            productos[str(i+1)] = [identificacion, nombre, precio, costo, stock]

        if opcion not in productos:
            return False, "❌ Producto invalido", None

        if cantidad_agregar <= 0:
            return False, "❌ Cantidad inválida", None 

        identificacion, nombre, precio, costo, stock = productos[opcion]
        nuevo_stock = stock + cantidad_agregar

        cursor.execute(
            'UPDATE productos SET cantidad = %s WHERE "identificación" = %s AND usuario_id = %s',
            (nuevo_stock, identificacion, usuario_id)
        )
        conn.commit()

        return True, f"✅ Nuevo stock {nombre}: {nuevo_stock}", nombre 

    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"❌ Error: {str(e)}", None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def obtener_productos_para_rellenar(get_conn, usuario_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT "identificación", nombre, precio, costo, cantidad FROM productos WHERE usuario_id = %s ORDER BY "identificación"',
            (usuario_id,)
        )
        lineas = cursor.fetchall()

        productos = {}
        for i, linea in enumerate(lineas):
            identificacion = linea[0]
            nombre = linea[1]
            precio = Decimal(linea[2])
            costo = Decimal(linea[3])
            stock = int(linea[4])
            productos[str(i+1)] = [identificacion, nombre, precio, costo, stock]

        return productos

    except Exception:
        return {}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
UPLOAD_FOLDER = os.path.abspath("static/logos")
ALLOWED_EXT = {'png','jpg','jpeg','webp'}
MAX_LOGO_SIZE = 2 * 1024 * 1024
MAX_PRECIO = Decimal('1000000')
MAX_CANTIDAD = 1000000
RESERVED_SLUGS = {'static','admin','api','login','entrar','pruebas','tienda','salir'}

logger = logging.getLogger(__name__)

def init_db():
    conn=None
    try:
        conn=get_conn()
        cur=conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS categorias (id SERIAL PRIMARY KEY, usuario_id TEXT NOT NULL, nombre TEXT NOT NULL)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_categorias_user_lower ON categorias (usuario_id, LOWER(nombre))")
        cur.execute("CREATE TABLE IF NOT EXISTS tiendas (id SERIAL PRIMARY KEY, usuario_id TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, slug TEXT UNIQUE NOT NULL, color TEXT NOT NULL, logo_path TEXT NOT NULL)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY, usuario_id TEXT NOT NULL, nombre TEXT NOT NULL,
                precio DECIMAL(12,2) NOT NULL, costo DECIMAL(12,2) NOT NULL,
                cantidad INTEGER NOT NULL, ganancia DECIMAL(12,2) NOT NULL,
                categoria_id INTEGER REFERENCES categorias(id), creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (cantidad >=0 AND cantidad <= 1000000), CHECK (precio >=0 AND precio <= 1000000)
            )
        """)
        conn.commit()
        cur.close()
    finally:
        if conn: conn.close()

def _safe_strip(v): return "" if v is None else str(v).strip()

def _to_decimal_safe(v):
    try:
        d=Decimal(str(v).strip())
        if not d.is_finite(): return None
        return d
    except: return None

def _normalize(s):
    s=_safe_strip(s).lower()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

STOPWORDS = {'para','con','sin','una','del','las','los','un','de','la','el','en','al','por','mas'}
COLORES_TALLAS = {'azul','rojo','negro','blanco','amarillo','gris','grande','chico','mini','mediano','pequeno','talla','xl'}

def _raiz(w):
    for suf in ('es','as','os','a','o','e','s'):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w

_FILTRO = {_raiz(w) for w in STOPWORDS | COLORES_TALLAS} | STOPWORDS | COLORES_TALLAS

def _palabras_significativas(texto):
    palabras = re.findall(r'[a-z]{2,}', _normalize(texto))
    return [_raiz(w) for w in palabras if _raiz(w) not in _FILTRO and w not in _FILTRO]

def _validar_logo_contenido(archivo, ext):
    try:
        firma=archivo.read(12)
        archivo.seek(0)
        if len(firma)<8: return False
        es_png=firma.startswith(b"\x89PNG\r\n\x1a\n")
        es_jpg=firma.startswith(b"\xff\xd8\xff")
        es_webp=firma[:4]==b"RIFF" and firma[8:12]==b"WEBP"
        if ext=='png': return es_png
        if ext in ('jpg','jpeg'): return es_jpg
        if ext=='webp': return es_webp
        return False
    except: return False

def crear_tienda_logica_completa(usuario_id, nombre_tienda, slug_tienda, descripcion, whatsapp, logo_file, banner_file, color=None):
    conn = None
    rutas_guardadas = [] # para borrar las 2 si falla
    try:
        slug_tienda = slug_tienda.lower().strip().replace(" ", "-")
        if "/" in slug_tienda:
            slug_tienda = slug_tienda.split("/")[-1]

        base = "static/uploads"
        os.makedirs(f"{base}/logos", exist_ok=True)
        os.makedirs(f"{base}/banners", exist_ok=True)

        logo_path = None
        banner_path = None

        if logo_file and logo_file.filename != '':
            fname = secure_filename(f"{slug_tienda}_logo_{logo_file.filename}")
            ruta_fs = f"{base}/logos/{fname}"
            logo_file.save(ruta_fs)
            rutas_guardadas.append(ruta_fs)
            logo_path = f"/{ruta_fs}"

        if banner_file and banner_file.filename != '':
            fname = secure_filename(f"{slug_tienda}_banner_{banner_file.filename}")
            ruta_fs = f"{base}/banners/{fname}"
            banner_file.save(ruta_fs)
            rutas_guardadas.append(ruta_fs)
            banner_path = f"/{ruta_fs}"

         DATABASE_URL = os.getenv("DATABASE_URL")
         conn = psycopg2.connect(DATABASE_URL)
         cur = conn.cursor()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tiendas (usuario_id, nombre, slug, descripcion, logo_path, banner_path, whatsapp)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (usuario_id, nombre_tienda, slug_tienda, descripcion, logo_path, banner_path, whatsapp))
        conn.commit()
        cur.close()
        return True, f"Tienda /t/{slug_tienda} creada"

    except pg_errors.UniqueViolation as e:
        if conn: conn.rollback()
        for r in rutas_guardadas:
            if os.path.exists(r): os.remove(r)
        cname = getattr(e.diag, 'constraint_name', '') or ''
        if cname == 'tiendas_slug_key': 
            return False, f"El link /t/{slug_tienda} ya está ocupado"
        if cname == 'tiendas_usuario_id_key':
            return False, "Ya tienes una tienda, borra la anterior para crear otra"
        return False, "Ese link o esa tienda ya existe"

    except Exception as ex:
        if conn: conn.rollback()
        for r in rutas_guardadas:
            if os.path.exists(r): os.remove(r)
        logger.exception("Error crear tienda")
        return False, f"No se pudo crear: {ex}"

    finally:
        if conn: conn.close()

def obtener_mi_tienda(usuario_id):
    conn=None
    try:
        conn=get_conn()
        cur=conn.cursor()
        cur.execute("SELECT nombre,slug,color,logo_path,banner_path FROM tiendas WHERE usuario_id=%s", (usuario_id,))
        fila=cur.fetchone()
        cur.close()
        if fila: return {"existe": True, "nombre": fila[0], "slug": fila[1], "color": fila[2], "logo": fila[3]}
        return {"existe": False}
    except Exception:
        logger.exception("Error obtener_mi_tienda")
        return {"existe": None, "error": "No se pudo verificar"}
    finally:
        if conn: conn.close()

def detectar_categoria_automatica(usuario_id, nombre_producto):
    palabras_nuevo=set(_palabras_significativas(nombre_producto))
    if not palabras_nuevo: return None
    conn=None
    try:
        conn=get_conn()
        cur=conn.cursor()
        cur.execute("SELECT c.nombre, p.nombre FROM productos p JOIN categorias c ON p.categoria_id=c.id WHERE p.usuario_id=%s AND LOWER(c.nombre)!='general' ORDER BY c.nombre, p.nombre", (usuario_id,))
        mejor={}
        for cat_ex, nombre_ex in cur.fetchall():
            palabras_ex=set(_palabras_significativas(nombre_ex))
            n=len(palabras_nuevo & palabras_ex)
            if n: mejor[cat_ex]=max(mejor.get(cat_ex,0), n)
        cur.close()
        if not mejor: return None
        max_n=max(mejor.values())
        ganadoras=[cat for cat,pts in mejor.items() if pts==max_n]
        if len(ganadoras)>1: return None
        return ganadoras[0]
    except Exception:
        logger.exception("Error detectar categoria")
        return None
    finally:
        if conn: conn.close()

def registrar_producto_con_categoria_auto(usuario_id, nombre, precio, costo, cantidad, categoria_texto=None):
    conn=None
    try:
        nombre=_safe_strip(nombre)
        categoria_texto=_safe_strip(categoria_texto)
        if not nombre or len(nombre)>100: return False, "Nombre inválido"
        precio_d=_to_decimal_safe(precio)
        costo_d=_to_decimal_safe(costo)
        if precio_d is None or costo_d is None: return False, "Precio o costo no es número válido"
        if precio_d>MAX_PRECIO or costo_d>MAX_PRECIO: return False, f"Precio máximo {MAX_PRECIO}"
        precio_d=precio_d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        costo_d=costo_d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if precio_d<=0: return False, "Precio debe ser mayor a 0"
        if costo_d<0 or costo_d>precio_d: return False, "Costo inválido"
        try: cantidad_i=int(str(cantidad).strip())
        except: return False, "Cantidad inválida"
        if cantidad_i<=0 or cantidad_i>MAX_CANTIDAD: return False, f"Cantidad 1-{MAX_CANTIDAD}"
        if not categoria_texto:
            categoria_texto=detectar_categoria_automatica(usuario_id, nombre) or "General"
        if len(categoria_texto)>50: return False, "Categoría muy larga (máx 50)"
        if not categoria_texto: categoria_texto="General"
        conn=get_conn()
        cur=conn.cursor()
        cur.execute("INSERT INTO categorias (usuario_id,nombre) VALUES (%s,%s) ON CONFLICT (usuario_id, LOWER(nombre)) DO UPDATE SET nombre=categorias.nombre RETURNING id, nombre", (usuario_id,categoria_texto))
        categoria_id,categoria_real=cur.fetchone()
        ganancia=(precio_d-costo_d).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        cur.execute("INSERT INTO productos (usuario_id,nombre,precio,costo,cantidad,ganancia,categoria_id) VALUES (%s,%s,%s,%s,%s,%s,%s)", (usuario_id,nombre,precio_d,costo_d,cantidad_i,ganancia,categoria_id))
        conn.commit()
        cur.close()
        return True, f"Producto en {categoria_real} registrado"
    except Exception:
        if conn: conn.rollback()
        logger.exception("Error registrar")
        return False, "No se pudo registrar"
    finally:
        if conn: conn.close()

def obtener_productos_agrupados_automatico(usuario_id):
    conn=None
    try:
        conn=get_conn()
        cur=conn.cursor()
        cur.execute("SELECT p.nombre,p.precio,p.cantidad,COALESCE(c.nombre,'General') FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id WHERE p.usuario_id=%s ORDER BY 4,1", (usuario_id,))
        filas=cur.fetchall()
        cur.close()
        agrupados={}
        for n,p,c,cat in filas: agrupados.setdefault(cat, []).append({"nombre":n,"precio":p,"cantidad":c})
        return agrupados
    except Exception:
        logger.exception("Error agrupados")
        return None
    finally:
        if conn: conn.close()

def obtener_tienda_publica_por_slug(slug):
    slug=_safe_strip(slug).lower()
    conn=None
    try:
        conn=get_conn()
        cur=conn.cursor()
        cur.execute("SELECT usuario_id,nombre,color,logo_path FROM tiendas WHERE slug=%s", (slug,))
        fila=cur.fetchone()
        if not fila:
            cur.close()
            return {"found": False}
        uid,nombre,color,logo=fila
        cur.execute("SELECT p.nombre,p.precio,COALESCE(c.nombre,'General') FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id WHERE p.usuario_id=%s ORDER BY 3,1", (uid,))
        prods=cur.fetchall()
        cur.close()
        agrupados={}
        for n,p,cat in prods: agrupados.setdefault(cat, []).append({"nombre":n,"precio":p})
        return {"found": True, "nombre":nombre,"color":color,"logo":logo,"productos":agrupados}
    except Exception:
        logger.exception("Error tienda publica")
        return {"found": None, "error": True}
    finally:
        if conn: conn.close()
