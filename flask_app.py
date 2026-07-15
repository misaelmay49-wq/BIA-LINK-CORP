from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify 
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from logica import registrar_producto, obtener_productos, procesar_venta_logica

app = Flask(__name__)
app.secret_key = 'bialink_clave_secreta_123'

def login_requerido(f):  
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/', methods=['GET', 'POST'])
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
            session['user_id'] = str(uuid.uuid4())
     
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

@app.route('/venta')
def registrar_venta():
    usuario_id = session.get('user_id', 'demo')
    print("BUSCANDO PRODUCTOS PARA:", usuario_id) 
    
    exito, mensaje, productos = obtener_productos(usuario_id)
    print("ENCONTRO:", len(productos), "productos") 
    
    return render_template('registrar_venta.html', productos=productos, active_page='venta')
    
@app.route('/procesar_venta', methods=['POST'])
def procesar_venta():
    usuario_id = session.get('user_id', 'demo')
    producto_id = request.form.get('producto_id', type=int)
    cantidad_vendida = request.form.get('cantidad', type=int)
    
    if not producto_id or not cantidad_vendida or cantidad_vendida <= 0:
        flash("❌ Selecciona un producto y cantidad válida", "error")
        return redirect(url_for('registrar_venta'))
    
    exito, mensaje = procesar_venta_logica(producto_id, cantidad_vendida, usuario_id)
    
    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "error")
    
    return redirect(url_for('registrar_venta'))

@app.route('/api/productos')
def api_productos():
    usuario_id = session.get('user_id', 'demo') # o como guardes el usuario
    if not usuario_id:
        return jsonify([])
    
    conn = get_conn()
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

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        
        hash_pass = generate_password_hash(password)
        
        conn = get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nombre, correo, password) VALUES (%s,%s,%s)", (nombre, correo, hash_pass))
            conn.commit()
            flash("✅ Usuario registrado. Ya puedes iniciar sesión", "success")
            return redirect(url_for('login'))
        except:
            flash("❌ Ese correo ya existe", "error")
        finally:
            cursor.close()
            conn.close()
    return render_template('registro.html')


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
        
        if user and check_password_hash(user[1], password): # user[0] = id
            session['user_id'] = user[0] # AQUI GUARDAMOS EL ID REAL
            return redirect(url_for('registrar_venta'))
        else:
            flash("❌ Correo o contraseña incorrecta", "error")
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))
