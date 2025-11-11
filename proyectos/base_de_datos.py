import sqlite3

def conectar():
    return sqlite3.connect("biblioteca.db")

def crear_tablas():
    conexion = conectar()
    cursor = conexion.cursor()

    # Tabla de usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('estudiante', 'docente', 'admin')) NOT NULL,
        contraseña TEXT NOT NULL
    )
    """)

    # Tabla de categorías
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    )
    """)

    # Tabla de libros (con columna categoria_id)
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
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
        FOREIGN KEY (id_libro) REFERENCES libros(id_libro)
    )
    """)

    conexion.commit()
    conexion.close()


def actualizar_tablas():
    """
    Agrega columnas nuevas si no existen,
    sin borrar la base ni los datos anteriores.
    """
    conexion = conectar()
    cursor = conexion.cursor()

    # Ejemplo: agregar columna 'categoria_id' si no existía antes
    columnas = [col[1] for col in cursor.execute("PRAGMA table_info(libros)").fetchall()]
    if 'categoria_id' not in columnas:
        cursor.execute("ALTER TABLE libros ADD COLUMN categoria_id INTEGER REFERENCES categorias(id_categoria)")
        print("Columna 'categoria_id' agregada a la tabla libros.")

    conexion.commit()
    conexion.close()
