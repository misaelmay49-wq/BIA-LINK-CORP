from flask import Flask, render_template, request, redirect, url_for, flash
import uuid
from logica import registrar_producto

app = Flask(__name__)
app.secret_key = 'bialink_clave_secreta_123'


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
        exito, msg = registrar_producto(usuario_id, nombre, precio, costo, cantidad)
        if exito:
            return redirect(url_for('exito'))
        else:
            flash(msg, "error")

    return render_template('registrar.html', active_page='registrar')

@app.route('/exito')
def exito():
       return render_template('exito.html', active_page='registrar')
