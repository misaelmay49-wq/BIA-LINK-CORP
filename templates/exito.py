DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIA LINK - Producto Registrado</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #111827;
            color: white;
            display: flex;
            min-height: 100vh;
        }
        .sidebar {
            width: 280px;
            background: #0F172A;
            padding: 25px 20px;
        }
        .logo {
            font-weight: bold;
            font-size: 22px;
            margin-bottom: 40px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .logo svg {
            width: 24px;
            height: 24px;
        }
        .menu-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            color: #94A3B8;
            text-decoration: none;
            cursor: pointer;
        }
        .menu-item:hover {
            background: #1F2937;
        }
        .menu-item.active {
            background: #2563EB;
            color: white;
        }
        .content {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            text-align: center;
        }
        .card {
            background: #1E3A8A;
            padding: 40px 30px;
            border-radius: 12px;
            width: 100%;
            max-width: 450px;
        }
        .card-logo {
            font-weight: bold;
            font-size: 20px;
            margin-bottom: 25px;
            text-align: left;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-logo svg {
            width: 22px;
            height: 22px;
        }
        .check {
            width: 60px;
            height: 60px;
            border: 3px solid #22C55E;
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            color: #22C55E;
        }
        h2 { color: #22C55E; margin-bottom: 15px; }
        p { color: #94A3B8; margin-bottom: 30px; }
        a.boton {
            display: block;
            width: 100%;
            padding: 14px;
            background: #2563EB;
            color: white;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
        }
        a.boton:hover { background: #1D4ED8; }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">
            BIA LINK
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="16" width="4" height="5" fill="white" opacity="0.8"/>
                <rect x="10" y="13" width="4" height="8" fill="white" opacity="0.8"/>
                <rect x="17" y="10" width="4" height="11" fill="white" opacity="0.8"/>
                <path d="M3 16L10 13L17 9L21 5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M17 5H21V9" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <a href="/" class="menu-item {% if active_page == 'registrar' %}active{% endif %}">➕ Registrar Producto</a>
        <div class="menu-item {% if active_page == 'venta' %}active{% endif %}">💰 Registrar Venta</div>
        <div class="menu-item {% if active_page == 'stock' %}active{% endif %}">📦 Rellenar Stock</div>
        <div class="menu-item {% if active_page == 'analisis' %}active{% endif %}">📊 Analizar Ventas</div>
        <div class="menu-item {% if active_page == 'dashboard' %}active{% endif %}">📈 Dashboard</div>
        <div class="menu-item {% if active_page == 'config' %}active{% endif %}">⚙️ Configuración</div>
    </div>

    <div class="content">
        <div class="card">
            <div class="card-logo">
                BIA LINK
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="16" width="4" height="5" fill="white" opacity="0.8"/>
                    <rect x="10" y="13" width="4" height="8" fill="white" opacity="0.8"/>
                    <rect x="17" y="10" width="4" height="11" fill="white" opacity="0.8"/>
                    <path d="M3 16L10 13L17 9L21 5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M17 5H21V9" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="check">✓</div>
            <h2>✅📦 Producto registrado correctamente</h2>
            <p>El producto se ha guardado exitosamente en el sistema.</p>
            <a href="/" class="boton">← Volver al inicio</a>
        </div>
    </div>
</body>
</html><!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIA LINK - Producto Registrado</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #111827;
            color: white;
            display: flex;
            min-height: 100vh;
        }
        .sidebar {
            width: 280px;
            background: #0F172A;
            padding: 25px 20px;
        }
        .logo {
            font-weight: bold;
            font-size: 22px;
            margin-bottom: 40px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .logo svg {
            width: 24px;
            height: 24px;
        }
        .menu-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            color: #94A3B8;
            text-decoration: none;
            cursor: pointer;
        }
        .menu-item:hover {
            background: #1F2937;
        }
        .menu-item.active {
            background: #2563EB;
            color: white;
        }
        .content {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            text-align: center;
        }
        .card {
            background: #1E3A8A;
            padding: 40px 30px;
            border-radius: 12px;
            width: 100%;
            max-width: 450px;
        }
        .card-logo {
            font-weight: bold;
            font-size: 20px;
            margin-bottom: 25px;
            text-align: left;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-logo svg {
            width: 22px;
            height: 22px;
        }
        .check {
            width: 60px;
            height: 60px;
            border: 3px solid #22C55E;
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            color: #22C55E;
        }
        h2 { color: #22C55E; margin-bottom: 15px; }
        p { color: #94A3B8; margin-bottom: 30px; }
        a.boton {
            display: block;
            width: 100%;
            padding: 14px;
            background: #2563EB;
            color: white;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
        }
        a.boton:hover { background: #1D4ED8; }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">
            BIA LINK
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="16" width="4" height="5" fill="white" opacity="0.8"/>
                <rect x="10" y="13" width="4" height="8" fill="white" opacity="0.8"/>
                <rect x="17" y="10" width="4" height="11" fill="white" opacity="0.8"/>
                <path d="M3 16L10 13L17 9L21 5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M17 5H21V9" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <a href="/" class="menu-item {% if active_page == 'registrar' %}active{% endif %}">➕ Registrar Producto</a>
        <div class="menu-item {% if active_page == 'venta' %}active{% endif %}">💰 Registrar Venta</div>
        <div class="menu-item {% if active_page == 'stock' %}active{% endif %}">📦 Rellenar Stock</div>
        <div class="menu-item {% if active_page == 'analisis' %}active{% endif %}">📊 Analizar Ventas</div>
        <div class="menu-item {% if active_page == 'dashboard' %}active{% endif %}">📈 Dashboard</div>
        <div class="menu-item {% if active_page == 'config' %}active{% endif %}">⚙️ Configuración</div>
    </div>

    <div class="content">
        <div class="card">
            <div class="card-logo">
                BIA LINK
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="16" width="4" height="5" fill="white" opacity="0.8"/>
                    <rect x="10" y="13" width="4" height="8" fill="white" opacity="0.8"/>
                    <rect x="17" y="10" width="4" height="11" fill="white" opacity="0.8"/>
                    <path d="M3 16L10 13L17 9L21 5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M17 5H21V9" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="check">✓</div>
            <h2>✅📦 Producto registrado correctamente</h2>
            <p>El producto se ha guardado exitosamente en el sistema.</p>
            <a href="/" class="boton">← Volver al inicio</a>
        </div>
    </div>
</body>
</html>
