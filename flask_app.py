
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify 
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta
import uuid
from decimal import Decimal, InvalidOperation
import psycopg2
from psycopg2.extras import RealDictCursor
from logica import registrar_producto, procesar_venta_logica, get_conn, analizar_ventas

app = Flask(__name__)
app.secret_key = 'bialink_clave_secreta_123'
app.permanent_session_lifetime = timedelta(days=30)

@app.route('/')
def inicio():
    if 'user_id' in session:
        return redirect(url_for('registrar'))
    return redirect(url_for('registro'))

def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            
            if request.path.startswith('/api/'):
                return jsonify({
                    "hay_ventas": False,
                    "mensaje": "Inicia sesión para continuar",
                    "total_dia": 0.0,
                    "productos": {},
                    "estado_dia": "error",
                    "sugerencias": [],
                    "error": "No autenticado"
                }), 401
        
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper
                            
def obtener_productos(usuario_id):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    try:
        cursor.execute("SELECT identificación, nombre, precio, costo, cantidad FROM productos WHERE usuario_id=%s AND cantidad > 0", (usuario_id,)) 
        productos = cursor.fetchall()
        return True, "Productos cargados", productos 
    except:
        return False, "Error al cargar productos", []
    finally:
        cursor.close()
        conn.close()

def obtener_producto_por_id(producto_id, usuario_id):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT identificación, nombre, precio, costo, cantidad 
            FROM productos 
            WHERE identificación = %s AND usuario_id = %s
        """, (producto_id, usuario_id))
        producto = cursor.fetchone()
        
        if not producto:
            return False, "Producto no encontrado", None
            
        return True, "Producto encontrado", producto
        
    except Exception as e:
        print("Error obtener_producto_por_id:", str(e))
        return False, "Error al buscar producto", None
    finally:
        cursor.close()
        conn.close()


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        try:
            nombre = request.form['nombre'].strip()
            precio = float(request.form['precio'])
            costo = float(request.form['costo'])
            cantidad = int(request.form['cantidad'])
        except ValueError:
            flash("❌ Precio, costo y cantidad deben ser números válidos", "error")
            return render_template('registrar.html', active_page='registrar')

        if not nombre:
            flash("❌ El nombre del producto no puede estar vacío", "error")
            return render_template('registrar.html', active_page='registrar')

        if len(nombre) > 50:
            flash("❌ El nombre no puede tener más de 50 caracteres", "error")
            return render_template('registrar.html', active_page='registrar')

        if precio <= 0:
            flash("❌ El precio debe ser mayor a 0", "error")
            return render_template('registrar.html', active_page='registrar')

        if costo < 0:
            flash("❌ El costo de producción no puede ser negativo", "error")
            return render_template('registrar.html', active_page='registrar')

        if costo > precio:
            flash("❌ El costo de producción no puede ser mayor al precio de venta", "error")
            return render_template('registrar.html', active_page='registrar')

        if cantidad <= 0:
            flash("❌ La cantidad debe ser mayor a 0", "error")
            return render_template('registrar.html', active_page='registrar')
      
              
        if 'user_id' not in session:
            return redirect(url_for('login'))  
    
        usuario_id = session['user_id']  
        exito, msg = registrar_producto(usuario_id, nombre, precio, costo, cantidad)            
        if exito:
            return redirect(url_for('exito'))
        else:
            flash(msg, "error")

    return render_template('registrar.html', active_page='registrar')

@app.route('/exito')
def exito():
       return render_template('exito.html', active_page='registrar')

@app.route('/exito_cuenta')
def exito_cuenta():
    return render_template('exito_cuenta.html', active_page='auth')

@app.route('/dashboard')
@login_requerido
def dashboard():
    usuario_id = session['user_id']
    exito, mensaje, productos = obtener_productos(usuario_id)
    return render_template('dashboard.html', productos=productos, active_page='dashboard')

@app.route('/procesar_venta', methods=['POST'])
@login_requerido
def procesar_venta():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    usuario_id = session['user_id']
    producto_id = request.form.get('producto_id', type=int)
    cantidad_vendida = request.form.get('cantidad', type=int)

    if not producto_id or not cantidad_vendida or cantidad_vendida <= 0:
        flash("❌ Selecciona un producto y cantidad válida", "error")
        return redirect(url_for('registrar_venta'))

    exito, mensaje = procesar_venta_logica(producto_id, cantidad_vendida, usuario_id)

    if exito:
        return render_template('venta_exito.html') 
    else:
        flash(mensaje, "error")
        return redirect(url_for('registrar_venta'))
                   
@app.route('/venta', methods=['GET', 'POST'])
@login_requerido
def registrar_venta():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuario_id = session['user_id']
    
    if request.method == 'POST':
        
        print("=== DATOS DEL FORM ===", request.form)
        
        producto_id = request.form.get('producto_id')
        cantidad = request.form.get('cantidad')
        
        print(f"Producto: {producto_id}, Cantidad: {cantidad}")
        
        if not all([producto_id, cantidad]):
            return "Faltan campos del formulario", 400
        
        producto_id = int(producto_id)
        cantidad = int(cantidad)
        
        exito, mensaje, producto = obtener_producto_por_id(producto_id, usuario_id)
        
        if not exito:
            flash(mensaje, 'error')
            return redirect(url_for('registrar_venta'))
        
        if producto['cantidad'] < cantidad:
            flash(f'Solo tienes {producto["cantidad"]} en stock', 'error')
            return redirect(url_for('registrar_venta'))
        
        precio = float(producto['precio'])
        costo = float(producto['costo'])
        total = precio * cantidad
        
        print(f"Venta OK: {producto['nombre']} x{cantidad} = ${total}")
        
        ganancia = (precio - costo) * cantidad
        
        conn = get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO ventas (usuario_id, producto_id, cantidad, precio_unitario, costo_unitario, total, ganancia, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (usuario_id, producto_id, cantidad, precio, costo, total, ganancia))
            
            cursor.execute("""
                UPDATE productos SET cantidad = cantidad - %s
                WHERE identificacion = %s AND usuario_id = %s
            """, (cantidad, producto_id, usuario_id))
            
            conn.commit()
            
            flash(f'Venta registrada: {producto["nombre"]} x {cantidad} = ${total}','success')
            return redirect(url_for('analizar_ventas'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error al guardar: {str(e)}', 'error')
            print('=== ERROR EN POST ===', str(e))
            return redirect(url_for('registrar_venta'))

        finally:
           cursor.close()
           conn.close()

       conn = get_conn()
       cursor = conn.cursor()
       cursor.exectue(" SELECT identificación, nombre, precio FROM productos WHERE usuario_id = %s",(usuario_id))
       productos = cursor.fetchall()
       cursor.close()
       conn.close()

       return render_template('venta_exito.html', productos=productos)
           
@app.route('/api/productos')
@login_requerido
def api_productos():
    if 'user_id' not in session:
        return jsonify([])

    usuario_id = session['user_id']
    conn=get_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    cursor.execute('SELECT "identificación", nombre, precio, costo, cantidad FROM productos WHERE usuario_id = %s AND cantidad > 0', (usuario_id,))
    productos = cursor.fetchall()
    cursor.close()
    conn.close()

    lista = []
    for p in productos:
        lista.append({
           'id': p['identificación'],
           'nombre': p['nombre'],
           'precio': float(p['precio'] or 0),
           'costo': float(p['costo'] or 0),
           'cantidad': p['cantidad'] or 0
        })
    return jsonify(lista)

@app.route('/registro',methods=['GET','POST'])
def registro():
    if 'user_id' in session:
        return redirect(url_for('registrar'))

    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        password_confirm = request.form['confirmar']
        nombre = correo.split('@')[0]

        if password!= password_confirm:
            flash("❌ Las contraseñas no coinciden", "error")
            return render_template('auth.html')

        hash_pass = generate_password_hash(password)
        conn = get_conn()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO usuarios (nombre, correo, password) VALUES (%s,%s,%s)", (nombre, correo, hash_pass))
            conn.commit()
            
            cursor.execute("SELECT id FROM usuarios WHERE correo=%s", (correo,))
            nuevo_user = cursor.fetchone()
            session.permanent = True
            session['user_id'] = nuevo_user[0]
            
            flash("✅ Usuario registrado. Ya puedes iniciar sesión", "success")
            return redirect(url_for('exito_cuenta'))
        except Exception as e:
            flash("❌ Ese correo ya existe", "error")
            print("ERROR BD:", e)
            flash(f"❌ Error: {e}","error")
        finally:
            cursor.close()
            conn.close()

    return render_template('auth.html')
            
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('registrar'))

    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM usuarios WHERE correo=%s", (correo,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user[1], password):
            session.permanent = True
            session['user_id'] = user[0]
            return redirect(url_for('login_exito')) 
        else:
            flash("❌ Correo o contraseña incorrecta", "error")
    return render_template('login.html')

@app.route('/login_exito')
@login_requerido
def login_exito():
    return render_template('login_exito.html')
            
@app.route('/logout')
@login_requerido
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/api/analisis-ventas')
@login_requerido
def api_analisis_ventas():
    try:
        usuario_id = session['user_id']
        hay_ventas, productos, total_dia = analizar_ventas(usuario_id, get_conn)

        if not hay_ventas:
            return jsonify({
                "hay_ventas": False,
                "mensaje": "No hay ventas registradas hoy",
                "total_dia": 0.0,
                "productos": {},
                "estado_dia": "sin_ventas",
                "sugerencias": ["Registra tu primera venta del día"]
            })

        productos_json = {}
        sugerencias = []

        for nombre, datos in productos.items():
            ganancia_neta = float(datos['ganancia_neta'])
            productos_json[nombre] = {
                "unidades": int(datos['unidades']),
                "ganancia_bruta": float(datos['ganancia_bruta']),
                "ganancia_neta": ganancia_neta,
                "rendimiento": datos['rendimiento']
            }
            if ganancia_neta < 300:
                sugerencias.append(f"Haz promoción en {nombre}")

        total_dia = float(total_dia)
        if total_dia >= 2000:
            estado = "excelente"
        elif total_dia >= 1000:
            estado = "bueno"
        else:
            estado = "bajo"

        return jsonify({
            "hay_ventas": True,
            "mensaje": "Ventas del día cargadas",
            "total_dia": total_dia,
            "productos": productos_json,
            "estado_dia": estado,
            "sugerencias": sugerencias
        })

    except Exception as e:
        print("❌ Error en /api/analisis-ventas:", e)
        return jsonify({
            "hay_ventas": False,
            "mensaje": "Error al cargar datos",
            "total_dia": 0.0,
            "productos": {},
            "estado_dia": "error",
            "sugerencias": [],
            "error": str(e)
        }), 500

@app.route('/analizar-ventas')  
@login_requerido
def analizar_ventas():
    return render_template('analizar_ventas.html')
