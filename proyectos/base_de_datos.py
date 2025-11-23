import sqlite3

# === Conexión a la base de datos ===
def conectar():
    return sqlite3.connect("Hope_library_system.db")


# === Crear tablas iniciales ===
def crear_tablas():
    conexion = conectar()
    cursor = conexion.cursor()

    # Tabla de usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('estudiante', 'docente', 'admin')) NOT NULL,
        contraseña TEXT NOT NULL,
        racha INTEGER DEFAULT 0
    )
    """)

    # Tabla de categorías
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    )
    """)

    # Tabla de libros
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS libros (
        id_libro INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT,
        titulo TEXT NOT NULL,
        autor TEXT,
        editorial TEXT,
        categoria_id INTEGER,
        ubicacion TEXT,
        precio REAL,
        cantidad_total INTEGER,
        cantidad_disponible INTEGER,
        cantidad_reservada INTEGER DEFAULT 0,
        estado TEXT,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id_categoria)
    )
    """)

    # Tabla de préstamos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario TEXT,
        id_libro INTEGER,
        fecha_prestamo TEXT,
        cantidad_prestada INTEGER,
        estado TEXT,
        dias_retraso INTEGER DEFAULT 0,
        monto_cobrado REAL DEFAULT 0,
        deposito REAL DEFAULT 0,
        deposito_pagado INTEGER DEFAULT 0,
        entrega_domicilio INTEGER DEFAULT 0,
        descuento_reposicion REAL DEFAULT 0,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
        FOREIGN KEY (id_libro) REFERENCES libros(id_libro)
    )
    """)

    # Tabla de depósitos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS depositos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario TEXT,
        id_libro INTEGER,
        monto REAL,
        fecha TEXT,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
        FOREIGN KEY (id_libro) REFERENCES libros(id_libro)
    )
    """)

    conexion.commit()
    conexion.close()


# === Actualizar estructura de tablas existentes ===
def actualizar_tablas():
    conexion = conectar()
    cursor = conexion.cursor()

    # === Tabla prestamos ===
    cursor.execute("PRAGMA table_info(prestamos)")
    columnas_prestamos = [col[1] for col in cursor.fetchall()]
    columnas_faltantes_prestamos = {
        "dias_retraso": "INTEGER DEFAULT 0",
        "monto_cobrado": "REAL DEFAULT 0",
        "deposito": "REAL DEFAULT 0",
        "deposito_pagado": "INTEGER DEFAULT 0",
        "entrega_domicilio": "INTEGER DEFAULT 0",
        "descuento_reposicion": "REAL DEFAULT 0"
    }
    for nombre, tipo in columnas_faltantes_prestamos.items():
        if nombre not in columnas_prestamos:
            cursor.execute(f"ALTER TABLE prestamos ADD COLUMN {nombre} {tipo}")
            print(f"[OK] Columna '{nombre}' agregada a prestamos")

    # === Tabla libros ===
    cursor.execute("PRAGMA table_info(libros)")
    columnas_libros = [col[1] for col in cursor.fetchall()]
    if "cantidad_reservada" not in columnas_libros:
        cursor.execute("ALTER TABLE libros ADD COLUMN cantidad_reservada INTEGER DEFAULT 0")
        print("[OK] Columna 'cantidad_reservada' agregada a libros")

    conexion.commit()
    conexion.close()


# === Guardar depósito ===
def guardar_deposito(id_usuario, id_libro, monto):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO depositos (id_usuario, id_libro, monto, fecha)
            VALUES (?, ?, ?, datetime('now'))
        """, (id_usuario, id_libro, monto))
        conexion.commit()
        print("[OK] Depósito registrado correctamente")
    except Exception as e:
        print("Error al guardar el depósito:", e)
    finally:
        conexion.close()

