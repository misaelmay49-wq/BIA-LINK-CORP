
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify 
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid
from logica import registrar_producto, procesar_venta_logica, get_conn

app = Flask(__name__)
app.secret_key = 'bialink_clave_secreta_123'

def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def obtener_productos(usuario_id):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nombre, precio FROM productos WHERE usuario_id=%s", (usuario_id,))
        productos = cursor.fetchall()
        return True, "Productos cargados", productos 
    except:
        return False, "Error al cargar productos", []
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

@app.route('/')
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
                   
@app.route('/venta')
@login_requerido
def registrar_venta():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    usuario_id = session['user_id']
    print("BUSCANDO PRODUCTOS PARA:", usuario_id)
    
    exito, mensaje, productos = obtener_productos(usuario_id)
    print("ENCONTRO:", len(productos), "productos") 
    
    return render_template('registrar_venta.html', productos=productos, active_page='venta')
        
@app.route('/api/productos')
@login_requerido
def api_productos():
    if 'user_id' not in session:
        return jsonify([])

    usuario_id = session['user_id']
    conn=get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, precio, costo, cantidad FROM productos WHERE usuario_id = %s", (usuario_id,))
    productos = cursor.fetchall()
    cursor.close()
    conn.close()

    lista = []
    for p in productos:
        lista.append({
            'id': p[0],
            'nombre': p[1],
            'precio': float(p[2]),
            'costo': float(p[3]),
            'cantidad': p[4]
        })
    return jsonify(lista)

@app.route('/registro',methods=['GET','POST'])
def registro():
 if 'user_id' in session:
     return redirect(url_for('login_exito'))

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
            flash("✅ Usuario registrado. Ya puedes iniciar sesión", "success")
            return redirect(url_for('exito_cuenta'))
        except:
            flash("❌ Ese correo ya existe", "error")
            print("ERROR BD:", e) 
            flash(f"❌ Error: {e}","error")
        finally:
            cursor.close()
            conn.close()
            return render_template('auth.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
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
