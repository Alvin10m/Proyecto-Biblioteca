import sqlite3
from datetime import datetime
from base_de_datos import conectar, crear_tablas, actualizar_tablas
import json
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os 


#utlidades#
def exportar_usuarios_a_json():
    """
    Exporta todos los registros de la tabla 'usuarios' a un archivo JSON.
    """
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        # 1. Ejecutar la consulta para obtener todos los usuarios
        cursor.execute("SELECT id, nombre, tipo, contraseña FROM usuarios")
        usuarios_db = cursor.fetchall()

        # Obtener los nombres de las columnas para usarlos como claves JSON
        nombres_columnas = [description[0] for description in cursor.description]

        # 2. Convertir los datos de la DB a una lista de diccionarios
        usuarios_json = []
        for fila in usuarios_db:
            # Crea un diccionario mapeando los nombres de columna a los valores de la fila
            usuario_dict = dict(zip(nombres_columnas, fila))
            usuarios_json.append(usuario_dict)

        # 3. Guardar la lista de diccionarios en un archivo JSON
        nombre_archivo = "usuarios_exportados.json"
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(usuarios_json, f, ensure_ascii=False, indent=4)

        print(f"\n Exportación exitosa. {len(usuarios_json)} usuarios exportados a '{nombre_archivo}'.")

    except sqlite3.OperationalError as e:
        print(f"\n Error al acceder a la base de datos: {e}")

    except Exception as e:
        print(f"\n Ocurrió un error inesperado: {e}")

    finally:
        conexion.close()

crear_tablas()

def pausar():
    input("\nPresiona ENTER para continuar...")

# === Registro ===
def registrar_usuario():
    conn = conectar()
    cur = conn.cursor()

    print("\n=== REGISTRO DE USUARIO ===")
    id_usuario = input("ID de usuario: ").strip()
    nombre = input("Nombre y apellido: ").strip()
    tipo = input("Tipo (estudiante/docente/admin): ").strip().lower()
    contraseña = input("Contraseña: ").strip()

    # Insertar el nuevo usuario con su ID manual
    try:
        cur.execute("""
            INSERT INTO usuarios (id, nombre, tipo, contraseña)
            VALUES (?, ?, ?, ?)
        """, (id_usuario, nombre, tipo, contraseña))
        conn.commit()
        print(f"\nUsuario '{nombre}' registrado como {tipo} con ID '{id_usuario}'.")

    except sqlite3.IntegrityError:
        print("\nEse ID ya existe. Elige otro.")

    finally:
        conn.close()

# === Login ===
def iniciar_sesion():
    conn = conectar()
    cur = conn.cursor()

    id_usuario = input("ID de usuario: ")
    contraseña = input("Contraseña: ")

    cur.execute("SELECT * FROM usuarios WHERE id = ? AND contraseña = ?", (id_usuario, contraseña))
    usuario = cur.fetchone()
    conn.close()

    if usuario:
        # Convertir la tupla a diccionario para acceder con claves
        usuario_dict = {
            'id': usuario[0],
            'nombre': usuario[1],
            'tipo': usuario[2],
            'contraseña': usuario[3]
        }
        print(f"\nBienvenido {usuario_dict['nombre']} ({usuario_dict['tipo']})\n")
        return usuario_dict
    else:
        print("Usuario o contraseña incorrectos.")
        return None

# === Libros ===
def agregar_libro():
    conn = conectar()
    cur = conn.cursor()

    print("\n=== AGREGAR LIBRO (INVENTARIO) ===")
    isbn = input("ISBN: ").strip()
    titulo = input("Título: ").strip()
    autor = input("Autor: ").strip()
    editorial = input("Editorial: ").strip()
    ubicacion = input("Ubicación (estante/sección): ").strip()
    precio = float(input("Precio de adquisición: "))
    cantidad = int(input("Cantidad de ejemplares: "))

    cur.execute("SELECT id_categoria, nombre FROM categorias")
    cats = cur.fetchall()

    if not cats:
        print("No hay categorías. Crea una primero.")
        conn.close()
        return

    print("Categorías disponibles:")
    for c in cats:
        print(f"{c[0]}. {c[1]}")

    cat_id = int(input("ID de categoría: "))

    try:
        cur.execute("""
            INSERT INTO libros (isbn, titulo, autor, editorial, categoria_id, ubicacion, precio, cantidad_total, cantidad_disponible, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'disponible')
        """, (isbn, titulo, autor, editorial, cat_id, ubicacion, precio, cantidad, cantidad))
        conn.commit()
        print("Libro agregado al inventario correctamente.")

    except sqlite3.Error as e:
        print(f"Error: {e}")

    finally:
        conn.close()

# === Mostrar inventario ===
def ver_inventario():
    """Muestra el inventario completo"""
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT l.id_libro, l.isbn, l.titulo, l.autor, c.nombre, l.ubicacion, l.cantidad_total, l.cantidad_disponible, l.estado, l.precio
        FROM libros l
        JOIN categorias c ON l.categoria_id = c.id_categoria
        ORDER BY l.titulo
    """)

    libros = cur.fetchall()
    conn.close()

    print("\n" + "="*130)
    print(" " * 50 + "INVENTARIO COMPLETO")
    print("="*130)
    print(f"{'ID':<4} {'ISBN':<13} {'Título':<30} {'Autor':<20} {'Categoría':<15} {'Ubicación':<12} {'Total':<5} {'Disp':<5} {'Estado':<12} {'Precio':<8}")
    print("-"*130)

    for libro in libros:
        id_lib, isbn, titulo, autor, cat, ubic, total, disp, estado, precio = libro
        print(f"{id_lib:<4} {isbn if isbn else 'N/A':<13} {titulo[:29]:<30} {autor[:19]:<20} {cat[:14]:<15} {ubic[:11]:<12} {total:<5} {disp:<5} {estado.capitalize():<12} ${precio:<7.2f}")

    print("="*130)

# === Actualización de libros por inventario ===
def actualizar_libro():
    """Actualiza un libro existente en el inventario"""
    ver_inventario()
    conn = conectar()
    cur = conn.cursor()

    try:
        id_libro = input("\nID del libro a actualizar: ").strip()
        cur.execute("SELECT * FROM libros WHERE id_libro = ?", (id_libro,))
        if not cur.fetchone():
            print("Libro no encontrado.")
            return

        print("Deja en blanco para no modificar.")

        campos = ['isbn', 'titulo', 'autor', 'editorial', 'ubicacion', 'precio', 'cantidad_total']
        valores = [input(f"Nuevo {campo}: ").strip() or None for campo in campos]

        updates = []
        params = []

        for campo, valor in zip(campos, valores):
            if valor is not None:
                updates.append(f"{campo} = ?")
                params.append(valor)

        if not updates:
            print("No se modificó nada.")
            return

        # Si se cambia cantidad_total
        if 'cantidad_total' in [c.split('=')[0].strip() for c in updates]:
            nueva_cantidad = int(valores[campos.index('cantidad_total')])
            cur.execute("SELECT cantidad_disponible FROM libros WHERE id_libro = ?", (id_libro,))
            disp_actual = cur.fetchone()[0]

            if nueva_cantidad < disp_actual:
                print(f"No se puede reducir el total por debajo de los prestados ({disp_actual}).")
                return

        query = f"UPDATE libros SET {', '.join(updates)} WHERE id_libro = ?"
        params.append(id_libro)

        cur.execute(query, params)
        conn.commit()
        print("Libro actualizado correctamente.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        conn.close()

# === Reabastecer biblioteca ===
def reabastecer_biblioteca():
    """
    Aumenta la cantidad disponible de un libro existente sin crear uno nuevo.
    """
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        print("\n=== REABASTECER BIBLIOTECA ===")
        opcion = input("Buscar por (1) ID o (2) ISBN: ").strip()

        if opcion == "1":
            id_libro = input("Ingrese el ID del libro: ").strip()
            cursor.execute("SELECT id_libro, titulo, cantidad_total, cantidad_disponible FROM libros WHERE id_libro = ?", (id_libro,))
        elif opcion == "2":
            isbn = input("Ingrese el ISBN del libro: ").strip()
            cursor.execute("SELECT id_libro, titulo, cantidad_total, cantidad_disponible FROM libros WHERE isbn = ?", (isbn,))
        else:
            print("Opción inválida.")
            conexion.close()
            return

        libro = cursor.fetchone()

        if not libro:
            print("No se encontró el libro.")
            conexion.close()
            return

        id_libro, titulo, total_actual, disp_actual = libro

        print(f"\nLibro encontrado: {titulo}")
        print(f"Cantidad total actual: {total_actual}")
        print(f"Cantidad disponible actual: {disp_actual}")

        try:
            agregar = int(input("\nIngrese la cantidad a agregar: "))
            if agregar <= 0:
                print("Debe agregar al menos 1 ejemplar.")
                conexion.close()
                return
        except ValueError:
            print("Entrada inválida. Debe ser un número.")
            conexion.close()
            return

        nuevo_total = total_actual + agregar
        nuevo_disponible = disp_actual + agregar

        cursor.execute("""
            UPDATE libros
            SET cantidad_total = ?, cantidad_disponible = ?
            WHERE id_libro = ?
        """, (nuevo_total, nuevo_disponible, id_libro))

        conexion.commit()

        print(f"\nSe agregaron {agregar} unidades del libro '{titulo}'.")
        print(f"Nuevo total: {nuevo_total} (disponibles: {nuevo_disponible})")

    except Exception as e:
        print(f"Error al reabastecer: {e}")

    finally:
        conexion.close()

# === Categorías ===
def agregar_categoria():
    conexion = conectar()
    cursor = conexion.cursor()

    nombre = input("Nombre de la nueva categoría: ").strip()

    try:
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        conexion.commit()
        print(f"Categoría '{nombre}' creada correctamente.")
    except sqlite3.IntegrityError:
        print("Esa categoría ya existe.")
    finally:
        conexion.close()

# === Mostrar categorías ===
def ver_categorias():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()
    conexion.close()

    if categorias:
        print("\n=== CATEGORÍAS ===")
        for c in categorias:
            print(f"{c[0]} — {c[1]}")
    else:
        print("No hay categorías registradas.")

# === Buscar libros ===

def buscar_libros():
    conn = conectar()
    cur = conn.cursor()

    termino = input("Buscar por título o autor: ").strip()
    like_term = f"%{termino}%"

    cur.execute("""
        SELECT id_libro, titulo, autor, editorial, ubicacion, cantidad_total, cantidad_disponible, cantidad_reservada
        FROM libros
        WHERE titulo LIKE ? OR autor LIKE ?
    """, (like_term, like_term))

    resultados = cur.fetchall()

    if not resultados:
        print("\nNo se encontraron libros con ese término.")
        conn.close()
        return

    print("\n=== RESULTADOS DE LA BÚSQUEDA ===")
    for id_libro, titulo, autor, editorial, ubicacion, total, disponible, reservada in resultados:
        if disponible > 0 and reservada == 0:
            estado = "Disponible"
        elif disponible == 0:
            estado = "Prestado"
        else:
            estado = "Reservado"

        print(
            f"\nID: {id_libro}\n"
            f"Título: {titulo}\n"
            f"Autor: {autor}\n"
            f"Editorial: {editorial}\n"
            f"Ubicación: {ubicacion}\n"
            f"Cantidad total: {total}\n"
            f"Disponibles: {disponible}\n"
            f"Reservados: {reservada}\n"
            f"Estado: {estado}\n"
            "-----------------------------------------------"
        )

    conn.close()

# === Mostrar usuario
def mostrar_usuarios():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT id, nombre, tipo FROM usuarios")
    usuarios = cur.fetchall()
    conn.close()

    print("\n=== USUARIOS REGISTRADOS ===")
    for u in usuarios:
        print(f"ID: {u[0]} | Nombre: {u[1]} | Tipo: {u[2]}")

# === Actualizar tablas de forma automática ===
def agregar_columna_si_no_existe(nombre_tabla, nombre_columna, tipo):
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(f"PRAGMA table_info({nombre_tabla})")
    columnas = [col[1] for col in cursor.fetchall()]

    if nombre_columna not in columnas:
        cursor.execute(f"ALTER TABLE {nombre_tabla} ADD COLUMN {nombre_columna} {tipo}")

    conexion.commit()
    conexion.close()


# === Actualización automática de tablas ===
def actualizar_tablas():
    """
    Revisa y agrega columnas faltantes automáticamente.
    """

    # === Columna para manejar reservas en libros ===
    agregar_columna_si_no_existe('libros', 'cantidad_reservada', 'INTEGER DEFAULT 0')

    # === Columna para manejar racha del usuario ===
    agregar_columna_si_no_existe('usuarios', 'racha', 'INTEGER DEFAULT 100')

    # === Columna para fecha límite en préstamos ===
    agregar_columna_si_no_existe('prestamos', 'fecha_limite', 'TEXT')

    # === Columna para registrar déposito en préstamos ===
    agregar_columna_si_no_existe('prestamos', 'deposito', 'REAL DEFAULT 0')

    # === Columna para registrar pago ===
    agregar_columna_si_no_existe('prestamos', 'deposito_pagado', 'INTEGER DEFAULT 0')

    # === Columna para registrar monto cobrado en devoluciones ===
    agregar_columna_si_no_existe('prestamos', 'monto_cobrado', 'REAL DEFAULT 0')


# === Ver libros por categorías ===
def ver_libros_por_categoria():
    conexion = conectar()
    cursor = conexion.cursor()

    # Mostrar categorías
    cursor.execute("SELECT id_categoria, nombre FROM categorias")
    categorias = cursor.fetchall()

    if not categorias:
        print("No hay categorías registradas.")
        conexion.close()
        return

    print("\n=== CATEGORÍAS DISPONIBLES ===")
    for id_categoria, nombre in categorias:
        print(f"{id_categoria}. {nombre}")

    try:
        id_categoria = int(input("\nIngrese el número de la categoría que desea ver: "))
    except ValueError:
        print("Entrada inválida. Debe ingresar un número.")
        conexion.close()
        return

    # Verificar categoría
    cursor.execute("SELECT nombre FROM categorias WHERE id_categoria = ?", (id_categoria,))
    categoria = cursor.fetchone()

    if categoria is None:
        print("Categoría no encontrada.")
        conexion.close()
        return

    nombre_categoria = categoria[0]

    # Obtener libros de la categoría
    cursor.execute("""
        SELECT id_libro, titulo, autor, editorial, cantidad_disponible, cantidad_reservada, ubicacion
        FROM libros
        WHERE categoria_id = ?
    """, (id_categoria,))
    libros = cursor.fetchall()

    print(f"\n=== LIBROS EN CATEGORÍA: {nombre_categoria.upper()} ===")
    
    if not libros:
        print("No hay libros registrados en esta categoría.")
    else:
        for id_libro, titulo, autor, editorial, cantidad_disponible, cantidad_reservada, ubicacion in libros:

            # Determinar el estado correctamente
            if cantidad_disponible > 0 and cantidad_reservada == 0:
                estado = "Disponible"
            elif cantidad_disponible == 0 and cantidad_reservada > 0:
                estado = "Reservado"
            else:
                estado = "Prestado"

            print(
                f"\nID: {id_libro}\n"
                f"Título: {titulo}\n"
                f"Autor: {autor}\n"
                f"Editorial: {editorial}\n"
                f"Ubicación: {ubicacion}\n"
                f"Cantidad disponible: {cantidad_disponible}\n"
                f"Estado: {estado}\n"
                "-----------------------------------------------"
            )

    conexion.close()



# === Mostrar libros por su id ===
def mostrar_libros_por_id():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id_libro, titulo, autor, disponible FROM libros")
    libros = cur.fetchall()
    conn.close()

    if libros:
        print("\n=== LISTA DE LIBROS POR ID ===")
        for libro in libros:
            print(f"ID: {libro[0]} | Título: {libro[1]} | Autor: {libro[2]} | Disponibles: {libro[3]}")
    else:
        print("No hay libros registrados.")

    pausar()

# === Préstamos ===
def solicitar_prestamo(usuario):
    conexion = conectar()
    cursor = conexion.cursor()

    # === Verificar préstamos vencidos ===
    cursor.execute("""
        SELECT COUNT(*) 
        FROM prestamos
        WHERE id_usuario = ? AND estado = 'aprobado' AND fecha_limite < date('now')
    """, (usuario['id'],))
    prestamos_vencidos = cursor.fetchone()[0]

    if prestamos_vencidos > 0:
        print(f"No puedes solicitar un nuevo préstamo. Tienes {prestamos_vencidos} libro(s) vencido(s) sin devolver.")
        conexion.close()
        return

    print("\n=== SOLICITAR PRÉSTAMO ===")
    print("¿Desea buscar por:")
    print("1. Título de libro")
    print("2. Categoría")
    opcion = input("→ ")

    if opcion == "2":
        cursor.execute("SELECT id_categoria, nombre FROM categorias")
        categorias = cursor.fetchall()
        if not categorias:
            print("No hay categorías registradas.")
            conexion.close()
            return

        print("\nCategorías disponibles:")
        for c in categorias:
            print(f"{c[0]}. {c[1]}")

        try:
            categoria_id = int(input("Ingrese el ID de la categoría: "))
        except ValueError:
            print("Entrada inválida.")
            conexion.close()
            return

        cursor.execute("""
            SELECT id_libro, titulo, autor, cantidad_disponible, cantidad_reservada
            FROM libros
            WHERE categoria_id = ?
        """, (categoria_id,))
        libros = cursor.fetchall()

        if not libros:
            print("No hay libros registrados en esa categoría.")
            conexion.close()
            return

        print("\nLibros disponibles en esa categoría:")
        for libro in libros:
            id_libro, titulo, autor, cantidad_disponible, cantidad_reservada = libro
            if cantidad_disponible > 0:
                estado = "Disponible"
            elif cantidad_reservada > 0:
                estado = "Reservado"
            else:
                estado = "Prestado"
            print(
                f"ID: {id_libro} — {titulo} ({autor}) — "
                f"Disponibles: {cantidad_disponible} — Reservados: {cantidad_reservada} — Estado: {estado}"
            )

        try:
            id_libro = int(input("\nIngrese el ID del libro que desea solicitar: "))
        except ValueError:
            print("ID inválido.")
            conexion.close()
            return

    else:
        titulo = input("Título del libro que desea solicitar: ")
        cursor.execute("""
            SELECT id_libro, titulo, cantidad_disponible, cantidad_reservada
            FROM libros
            WHERE LOWER(titulo) LIKE LOWER(?)
        """, (f"%{titulo}%",))
        libro = cursor.fetchone()

        if libro is None:
            print("No se encontró ningún libro con ese título.")
            conexion.close()
            return

        id_libro, titulo_libro, disponible, reservados = libro
        estado = "Disponible" if disponible > 0 else ("Reservado" if reservados > 0 else "Prestado")
        if disponible <= 0:
            print(f"El libro '{titulo_libro}' no está disponible actualmente. Estado: {estado}")
            if input("¿Desea reservarlo? (s/n): ").lower() == "s":
                try:
                    cantidad_reservar = int(input("¿Cuántos ejemplares desea reservar?: "))
                    cursor.execute("""
                        UPDATE libros
                        SET cantidad_reservada = cantidad_reservada + ?
                        WHERE id_libro = ?
                    """, (cantidad_reservar, id_libro))
                    conexion.commit()
                    print(f"Se han reservado {cantidad_reservar} ejemplares de '{titulo_libro}'.")
                except ValueError:
                    print("Cantidad inválida. Cancelando reserva.")
            conexion.close()
            return

    # === Cantidad solicitada ===
    try:
        cantidad_deseada = int(input("¿Cuántos ejemplares desea solicitar?: "))
    except ValueError:
        print("Cantidad no válida.")
        conexion.close()
        return

    cursor.execute("SELECT cantidad_disponible, titulo, precio FROM libros WHERE id_libro = ?", (id_libro,))
    libro_info = cursor.fetchone()

    if not libro_info:
        print("Libro no encontrado.")
        conexion.close()
        return

    cantidad_disponible, titulo_libro, precio_libro = libro_info

    if cantidad_deseada > cantidad_disponible:
        print(f"Solo hay {cantidad_disponible} ejemplares disponibles de '{titulo_libro}'.")
        conexion.close()
        return

    # === Obtener racha ===
    cursor.execute("SELECT racha FROM usuarios WHERE id = ?", (usuario['id'],))
    racha = cursor.fetchone()[0]

    # === Depósito obligatorio si racha <= 80 ===
    deposito = 0
    if racha <= 80:
        deposito = precio_libro * 0.40
        print(f"\nTu racha es {racha}. Debes pagar un depósito obligatorio de: ${deposito:.2f}")

        if cantidad_deseada > 1:
            print("Como tu racha es baja, solo puedes solicitar 1 ejemplar.")
            cantidad_deseada = 1

        pagar = input(f"¿Desea pagar ahora el depósito de ${deposito:.2f}? (s/n): ").lower()

        if pagar != 's':
            print("No puedes continuar sin pagar el depósito.")
            conexion.close()
            return

        cursor.execute("""
            INSERT INTO depositos (id_usuario, id_libro, monto, fecha)
            VALUES (?, ?, ?, datetime('now'))
        """, (usuario['id'], id_libro, deposito))
        conexion.commit()
        print("Depósito registrado correctamente.")

    # === Beneficios según racha ===
    dias_extra = 0
    beneficios = {
        "entrega_domicilio": 0,
        "descuento_reposicion": 0.0
    }

    if 150 < racha < 200:
        dias_extra = 1
        beneficios["entrega_domicilio"] = 1
        beneficios["descuento_reposicion"] = 0.2
    elif racha >= 200:
        dias_extra = 2
        beneficios["entrega_domicilio"] = 1
        beneficios["descuento_reposicion"] = 0.2

    # === Registrar préstamo ===
    try:
        cursor.execute("""
            INSERT INTO prestamos (
                id_usuario, id_libro, fecha_prestamo, cantidad_prestada, estado, deposito,
                entrega_domicilio, descuento_reposicion, deposito_pagado
            )
            VALUES (?, ?, date('now'), ?, 'pendiente', ?, ?, ?, 0)
        """, (
            usuario['id'], id_libro, cantidad_deseada, deposito,
            beneficios["entrega_domicilio"], beneficios["descuento_reposicion"]
        ))

        # Fecha límite
        fecha_limite_sql = "+2 days" if usuario['tipo'] == "estudiante" else "+5 days"

        cursor.execute(f"""
            UPDATE prestamos
            SET fecha_limite = date('now', '{fecha_limite_sql}', '+{dias_extra} days')
            WHERE id = (SELECT MAX(id) FROM prestamos)
        """)

        # Marcar que pagó depósito
        if deposito > 0:
            cursor.execute("""
                UPDATE prestamos
                SET deposito_pagado = 1
                WHERE id = (SELECT MAX(id) FROM prestamos)
            """)
            conexion.commit()

        # Actualizar disponibilidad
        cursor.execute("""
            UPDATE libros
            SET cantidad_disponible = cantidad_disponible - ?
            WHERE id_libro = ?
        """, (cantidad_deseada, id_libro))

        # Reducir reservas
        cursor.execute("SELECT cantidad_reservada FROM libros WHERE id_libro = ?", (id_libro,))
        cantidad_reservada = cursor.fetchone()[0]

        if cantidad_reservada > 0:
            reducir = min(cantidad_deseada, cantidad_reservada)
            cursor.execute("""
                UPDATE libros
                SET cantidad_reservada = cantidad_reservada - ?
                WHERE id_libro = ?
            """, (reducir, id_libro))

        # Actualizar estado final del libro
        cursor.execute("""
            SELECT cantidad_disponible, cantidad_reservada 
            FROM libros WHERE id_libro = ?
        """, (id_libro,))
        cant_final, cant_reservada = cursor.fetchone()

        if cant_final == 0 and cant_reservada > 0:
            estado = "reservado"
        elif cant_final == 0:
            estado = "prestado"
        else:
            estado = "disponible"

        cursor.execute("UPDATE libros SET estado = ? WHERE id_libro = ?", (estado, id_libro))

        conexion.commit()
        print(f"\nSolicitud registrada: {cantidad_deseada} ejemplar(es) de '{titulo_libro}'.")

    except sqlite3.Error as e:
        conexion.rollback()
        print(f"Error al registrar el préstamo: {e}")

    finally:
        conexion.close()


# === Devolución de libros ===

def devolver_libro(usuario):
    conexion = conectar()
    cursor = conexion.cursor()

    # === Obtener préstamos activos del usuario ===
    cursor.execute("""
        SELECT p.id, l.titulo, p.cantidad_prestada, l.precio, p.deposito, p.deposito_pagado
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.id_usuario = ? AND p.estado = 'aprobado'
    """, (usuario['id'],))
    prestamos = cursor.fetchall()

    if not prestamos:
        print("No tienes préstamos activos.")
        conexion.close()
        return

    print("\n=== DEVOLUCIÓN DE LIBROS ===")
    for p in prestamos:
        print(f"ID {p[0]} — {p[1]} — Cantidad: {p[2]} — Precio: ${p[3]:.2f}")

    try:
        id_prestamo = int(input("\nIngrese el ID del préstamo que desea devolver: "))
    except ValueError:
        print("ID inválido.")
        conexion.close()
        return

    # === Verificar préstamo seleccionado ===
    cursor.execute("""
        SELECT p.id_libro, p.cantidad_prestada, l.titulo, l.precio,
               p.deposito, p.deposito_pagado, p.fecha_limite
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.id = ? AND p.id_usuario = ?
    """, (id_prestamo, usuario['id']))
    prestamo_info = cursor.fetchone()

    if not prestamo_info:
        print("Préstamo no encontrado.")
        conexion.close()
        return

    id_libro, cantidad, titulo_libro, precio_libro, deposito, deposito_pagado, fecha_limite = prestamo_info

    # === Calcular días de retraso ===
    cursor.execute("SELECT julianday(date('now')) - julianday(?)", (fecha_limite,))
    dias_retraso = cursor.fetchone()[0]
    dias_retraso = int(dias_retraso) if dias_retraso and dias_retraso > 0 else 0
    multa_retraso = dias_retraso * 10  
    if multa_retraso > 0:
        print(f"\n⚠ Tienes {dias_retraso} día(s) de retraso. Multa: ${multa_retraso:.2f}")

    # === Racha del usuario ===
    cursor.execute("SELECT racha FROM usuarios WHERE id = ?", (usuario['id'],))
    racha = cursor.fetchone()[0]

    descuento_racha = 0
    if racha >= 150:
        descuento_racha = 0.20  
    elif racha <= 80:
        descuento_racha = 0

    # === Registrar estado de devolución ===
    print("\n¿En qué estado devuelves el libro?")
    print("1. En buen estado")
    print("2. Dañado (50% del precio)")
    print("3. Perdido (100% del precio)")
    estado_opcion = input("→ ")

    if estado_opcion == "1":
        estado_libro = "devuelto"
        monto_base = 0
    elif estado_opcion == "2":
        estado_libro = "dañado"
        monto_base = precio_libro * 0.50 * cantidad
    elif estado_opcion == "3":
        estado_libro = "perdido"
        monto_base = precio_libro * cantidad
    else:
        print("Opción inválida.")
        conexion.close()
        return

    # === Aplicar descuento por racha ===
    if estado_libro in ["dañado", "perdido"] and descuento_racha > 0:
        monto_base *= (1 - descuento_racha)
        print(f"✔ Se aplicó descuento de {descuento_racha*100:.0f}% por racha.")

    # === Sumar multa por retraso ===
    monto_total = monto_base + multa_retraso

    # === Restar depósito si fue pagado ===
    if deposito_pagado == 1:
        monto_total = max(0, monto_total - deposito)
        print(f"✔ Se descontó depósito pagado: ${deposito:.2f}")

    print(f"\nMonto total a pagar: ${monto_total:.2f}")

    try:
        # === Actualizar préstamo ===
        cursor.execute("""
            UPDATE prestamos
            SET estado = ?, monto_cobrado = ?, dias_retraso = ?
            WHERE id = ?
        """, (estado_libro, monto_total, dias_retraso, id_prestamo))

        # === Actualizar inventario ===
        if estado_libro != "perdido":
            cursor.execute("""
                UPDATE libros
                SET cantidad_disponible = cantidad_disponible + ?
                WHERE id_libro = ?
            """, (cantidad, id_libro))

        # === Actualizar estado general del libro ===
        cursor.execute("""
            SELECT cantidad_disponible, cantidad_reservada
            FROM libros
            WHERE id_libro = ?
        """, (id_libro,))
        disponible, reservada = cursor.fetchone()

        if disponible == 0 and reservada > 0:
            nuevo_estado = "reservado"
        elif disponible == 0:
            nuevo_estado = "prestado"
        else:
            nuevo_estado = "disponible"

        cursor.execute("UPDATE libros SET estado = ? WHERE id_libro = ?", (nuevo_estado, id_libro))

        conexion.commit()
        print(f"\n✔ Devolución registrada. Estado: {estado_libro}. Total a pagar: ${monto_total:.2f}")

    except Exception as e:
        conexion.rollback()
        print("Error al procesar devolución:", e)

    finally:
        conexion.close()




# === Ver préstamos de un usuario ===
def ver_prestamos_usuario(usuario):
    """
    Muestra los préstamos del usuario recibido como diccionario {'id': ..., 'nombre': ..., 'tipo': ...}
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT p.id, l.titulo, p.fecha_prestamo, p.fecha_limite, p.cantidad_prestada, p.estado
            FROM prestamos p
            LEFT JOIN libros l ON p.id_libro = l.id_libro
            WHERE p.id_usuario = ?
            ORDER BY p.fecha_prestamo DESC
        """, (usuario['id'],))
        prestamos = cursor.fetchall()

        if not prestamos:
            print("\nNo tienes préstamos registrados.")
            return

        print("\n=== MIS PRÉSTAMOS ===")
        for pid, titulo, fecha_prestamo, fecha_limite, cantidad, estado in prestamos:
            titulo_display = titulo if titulo else "Título desconocido"
            fecha_prestamo_display = fecha_prestamo if fecha_prestamo else "N/A"
            fecha_limite_display = fecha_limite if fecha_limite else "N/A"
            print(
                f"\nID préstamo: {pid}\n"
                f"Título: {titulo_display}\n"
                f"Cantidad: {cantidad}\n"
                f"Fecha de préstamo: {fecha_prestamo_display}\n"
                f"Fecha límite: {fecha_limite_display}\n"
                f"Estado: {estado}\n"
                "-----------------------------------------------"
            )

    except Exception as e:
        print(f"Error al obtener préstamos: {e}")
    finally:
        conexion.close()


# === Función para generar PDF ===
def generar_pdf(df, nombre_archivo="reporte_prestamos.pdf"):
    """
    Genera un PDF con tabla de los préstamos.
    """
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # === Título ===
    titulo = Paragraph("Reporte de Préstamos", styles['Title'])
    elements.append(titulo)
    elements.append(Spacer(1, 12))

    # === Preparar datos de la tabla ===
    data = [df.columns.tolist()] + df.values.tolist()

    # === Crear tabla ===
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(table)

    # === Construir PDF ===
    doc.build(elements)
    print(f"PDF generado: '{nombre_archivo}'")

# === Función para aprobar/rechazar préstamos y generar reportes ===
def aprobar_prestamos():
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        # === Traer todos los préstamos ===
        cursor.execute("""
            SELECT 
                p.id,
                p.id_usuario,
                u.nombre,
                u.tipo,
                u.racha,
                p.id_libro,
                l.titulo,
                p.cantidad_prestada,
                p.fecha_prestamo,
                p.estado
            FROM prestamos p
            LEFT JOIN usuarios u ON p.id_usuario = u.id
            LEFT JOIN libros l ON p.id_libro = l.id_libro
            ORDER BY p.fecha_prestamo ASC
        """)
        prestamos = cursor.fetchall()

        if not prestamos:
            print("\nNo hay préstamos registrados.")
        else:
            print("\n=== LISTA DE PRÉSTAMOS ===")
            for p in prestamos:
                print(
                    f"\nID PRÉSTAMO: {p[0]}\n"
                    f"Usuario: {p[2]} (ID: {p[1]})\n"
                    f"Tipo: {p[3]} | Racha: {p[4]}\n"
                    f"Libro: {p[6]} (ID: {p[5]})\n"
                    f"Cantidad: {p[7]} | Fecha: {p[8]} | Estado: {p[9]}\n"
                    "-----------------------------------------------"
                )

        # === Procesar préstamos pendientes ===
        while True:
            seleccion = input("\nIngrese el ID del préstamo a procesar (o 'q' para salir): ").strip()
            if seleccion.lower() == 'q':
                break

            try:
                id_prestamo = int(seleccion)
            except ValueError:
                print("ID inválido.")
                continue

            cursor.execute("""
                SELECT id_libro, cantidad_prestada, estado
                FROM prestamos
                WHERE id = ?
            """, (id_prestamo,))
            fila = cursor.fetchone()

            if not fila:
                print("Préstamo no encontrado.")
                continue

            id_libro, cantidad_prestada, estado_actual = fila

            if estado_actual != "pendiente":
                print("Ese préstamo ya fue procesado.")
                continue

            accion = input("¿Aprobar (a) / Rechazar (r) / Cancelar (c)?: ").strip().lower()

            if accion == 'a':
                cursor.execute("SELECT cantidad_disponible FROM libros WHERE id_libro = ?", (id_libro,))
                cantidad_disponible = cursor.fetchone()[0]

                if cantidad_disponible >= cantidad_prestada:
                    cursor.execute("""
                        UPDATE libros
                        SET cantidad_disponible = cantidad_disponible - ?
                        WHERE id_libro = ?
                    """, (cantidad_prestada, id_libro))

                    cursor.execute("""
                        SELECT cantidad_disponible, cantidad_reservada
                        FROM libros
                        WHERE id_libro = ?
                    """, (id_libro,))
                    disponible, reservada = cursor.fetchone()

                    if disponible == 0 and reservada > 0:
                        nuevo_estado = "reservado"
                    elif disponible == 0:
                        nuevo_estado = "prestado"
                    else:
                        nuevo_estado = "disponible"

                    cursor.execute("UPDATE libros SET estado = ? WHERE id_libro = ?", (nuevo_estado, id_libro))
                    cursor.execute("UPDATE prestamos SET estado = 'aprobado' WHERE id = ?", (id_prestamo,))
                    conexion.commit()
                    print(f"Préstamo {id_prestamo} aprobado correctamente.")
                else:
                    print("No hay suficientes ejemplares disponibles para aprobar este préstamo.")

            elif accion == 'r':
                try:
                    cursor.execute("""
                        UPDATE libros
                        SET cantidad_disponible = cantidad_disponible + ?
                        WHERE id_libro = ?
                    """, (cantidad_prestada, id_libro))

                    cursor.execute("""
                        SELECT cantidad_disponible, cantidad_reservada
                        FROM libros
                        WHERE id_libro = ?
                    """, (id_libro,))
                    disponible, reservada = cursor.fetchone()

                    if disponible == 0 and reservada > 0:
                        nuevo_estado = "reservado"
                    elif disponible == 0:
                        nuevo_estado = "prestado"
                    else:
                        nuevo_estado = "disponible"

                    cursor.execute("UPDATE libros SET estado = ? WHERE id_libro = ?", (nuevo_estado, id_libro))
                    cursor.execute("UPDATE prestamos SET estado = 'rechazado' WHERE id = ?", (id_prestamo,))
                    conexion.commit()
                    print(f"Préstamo {id_prestamo} rechazado y se devolvieron {cantidad_prestada} ejemplares al inventario.")
                except Exception as e:
                    conexion.rollback()
                    print("Error al rechazar préstamo:", e)
            else:
                print("Acción cancelada.")

        # === Generar reporte al finalizar ===
        opcion_reporte = input("\nDesea generar un reporte? (Excel, PDF, Ambos, No): ").strip().lower()
        if opcion_reporte in ['excel', 'pdf', 'ambos']:
            df = pd.read_sql_query("""
                SELECT p.id, u.nombre AS usuario, u.tipo, u.racha,
                       l.titulo AS libro, p.cantidad_prestada AS cantidad,
                       p.estado, p.fecha_prestamo AS fecha
                FROM prestamos p
                LEFT JOIN usuarios u ON p.id_usuario = u.id
                LEFT JOIN libros l ON p.id_libro = l.id_libro
                ORDER BY p.fecha_prestamo ASC
            """, conexion)

            # Crear carpeta en escritorio
            escritorio = os.path.join(os.path.expanduser("~"), "Escritorio")
            carpeta_reportes = os.path.join(escritorio, "reportes")
            os.makedirs(carpeta_reportes, exist_ok=True)

            if opcion_reporte in ['excel', 'ambos']:
                ruta_excel = os.path.join(carpeta_reportes, "reporte_prestamos.xlsx")
                df.to_excel(ruta_excel, index=False)
                print(f"Excel generado en: {ruta_excel}")

            if opcion_reporte in ['pdf', 'ambos']:
                ruta_pdf = os.path.join(carpeta_reportes, "reporte_prestamos.pdf")
                generar_pdf(df, nombre_archivo=ruta_pdf)
                print(f"PDF generado en: {ruta_pdf}")

    except Exception as e:
        print("Error al procesar préstamos:", e)
    finally:
        conexion.close()


# === Generar reporte desde el menú de administrador ===

def generar_reporte_admin():
    import os
    conexion = conectar()
    try:
        df = pd.read_sql_query("""
            SELECT p.id, u.nombre AS usuario, u.tipo, u.racha,
                   l.titulo AS libro, p.cantidad_prestada AS cantidad,
                   p.estado, p.fecha_prestamo AS fecha
            FROM prestamos p
            LEFT JOIN usuarios u ON p.id_usuario = u.id
            LEFT JOIN libros l ON p.id_libro = l.id_libro
            ORDER BY p.fecha_prestamo ASC
        """, conexion)

        if df.empty:
            print("No hay préstamos registrados.")
            return

        # === Crear carpeta "reportes" en el escritorio ===
        escritorio = os.path.join(os.path.expanduser("~"), "Escritorio")
        carpeta_reportes = os.path.join(escritorio, "reportes")
        if not os.path.exists(carpeta_reportes):
            os.makedirs(carpeta_reportes)
        print("Carpeta de reportes en:", carpeta_reportes)

        opcion_reporte = input("¿Desea generar un reporte? (Excel, PDF, Ambos, No): ").strip().lower()

        if opcion_reporte in ['excel', 'ambos']:
            ruta_excel = os.path.join(carpeta_reportes, "reporte_prestamos.xlsx")
            df.to_excel(ruta_excel, index=False)
            print(f"Excel generado en: {ruta_excel}")

        if opcion_reporte in ['pdf', 'ambos']:
            ruta_pdf = os.path.join(carpeta_reportes, "reporte_prestamos.pdf")
            generar_pdf(df, nombre_archivo=ruta_pdf)

    except Exception as e:
        print("Error al generar reporte:", e)
    finally:
        conexion.close()




# === Reporte de ingresos ===

def reporte_ingresos():
    conexion = conectar()
    cursor = conexion.cursor()

    print("\n=== REPORTE DE INGRESOS ===")

    # === Depósitos ===
    cursor.execute("""
        SELECT d.id, u.nombre, l.titulo, d.monto, d.fecha
        FROM depositos d
        JOIN usuarios u ON d.id_usuario = u.id
        JOIN libros l ON d.id_libro = l.id_libro
        ORDER BY d.fecha DESC
    """)
    depositos = cursor.fetchall()

    total_depositos = sum([d[3] for d in depositos]) if depositos else 0

    print("\n--- DEPÓSITOS ---")
    if depositos:
        for id_dep, usuario, libro, monto, fecha in depositos:
            print(f"[{id_dep}] {usuario} — {libro} — ${monto:.2f} — {fecha}")
    else:
        print("No hay depósitos registrados.")

    print(f"TOTAL DEPÓSITOS: ${total_depositos:.2f}")

    # === Multas y reposiciones ===
    cursor.execute("""
        SELECT p.id, u.nombre, l.titulo, p.monto_cobrado, p.estado, p.fecha_limite
        FROM prestamos p
        JOIN usuarios u ON p.id_usuario = u.id
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.monto_cobrado > 0
        ORDER BY p.id DESC
    """)
    cobros = cursor.fetchall()

    total_cobros = sum([c[3] for c in cobros]) if cobros else 0

    print("\n--- MULTAS Y REPOSICIONES ---")
    if cobros:
        for pid, usuario, libro, monto, estado, fecha_limite in cobros:
            print(f"[{pid}] {usuario} — {libro} — {estado} — ${monto:.2f}")
    else:
        print("No hay multas ni reposiciones registradas.")

    print(f"TOTAL MULTAS/REPOSICIONES: ${total_cobros:.2f}")

    # === Total general ===
    print("\n===============================")
    print(f"TOTAL GENERAL: ${total_depositos + total_cobros:.2f}")
    print("===============================\n")

    conexion.close()


# === Menús según tipo de usuario ===

def menu_admin(usuario):
    while True:
        print("\n=== MENÚ DEL ADMINISTRADOR ===")
        print("1. Agregar libro")
        print("2. Mostrar usuarios")
        print("3. Aprobar préstamos")
        print("4. Buscar libros")
        print("5. Ver inventario completo")
        print("6. Actualizar libro")
        print("7. Exportar Usuarios a JSON")
        print("8. Agregar categoría")
        print("9. Ver categorías")
        print("10. Reabastecer biblioteca")
        print("11. Generar reporte en PDF o Excel")
        print("12. Cerrar sesión")
        opcion = input("→ ")

        if opcion == "1":
            agregar_libro()
        elif opcion == "2":
            mostrar_usuarios()
        elif opcion == "3":
            aprobar_prestamos()
        elif opcion == "4":
            buscar_libros()
        elif opcion == "5":
            ver_inventario()
        elif opcion == "6":
            actualizar_libro()
        elif opcion == "7":
            exportar_usuarios_a_json()
        elif opcion == "8":
            agregar_categoria()
        elif opcion == "9":
            ver_categorias()
        elif opcion == "10":
            reabastecer_biblioteca()
        elif opcion == "11":
            generar_reporte_admin()
        elif opcion == "12":
            break

def menu_docente(usuario):
    while True:
        print("\n=== MENÚ DEL DOCENTE ===")
        print("1. Buscar libros")
        print("2. Ver libros por categoría")
        print("3. Solicitar préstamo")
        print("4. Ver mis préstamos")
        print("5. Devolver libro")
        print("6. Cerrar sesión")
        opcion = input("→ ")

        if opcion == "1":
            buscar_libros()
        elif opcion == "2":
            ver_libros_por_categoria()
        elif opcion == "3":
            solicitar_prestamo(usuario)
        elif opcion == "4":
            ver_prestamos_usuario(usuario)
        elif opcion == "5":
            devolver_libro(usuario)  
        elif opcion == "6":
            break
        else:
            print("Opción inválida.")


def menu_estudiante(usuario):
    while True:
        print("\n=== MENÚ DEL ESTUDIANTE ===")
        print("1. Buscar libros")
        print("2. Ver libros por categoría")
        print("3. Solicitar préstamo")
        print("4. Ver mis préstamos")
        print("5. Devolver libro")
        print("6. Cerrar sesión")
        opcion = input("→ ")

        if opcion == "1":
            buscar_libros()
        elif opcion == "2":
            ver_libros_por_categoria()
        elif opcion == "3":
            solicitar_prestamo(usuario)
        elif opcion == "4":
            ver_prestamos_usuario(usuario)
        elif opcion == "5":
            devolver_libro(usuario) 
        elif opcion == "6":
            break
        else:
            print("Opción inválida.")

# === Menú Principal ===
def menu_principal():
    while True:
        print("\n=== Hope library system ===")
        print("1. Registrar usuario")
        print("2. Iniciar sesión")
        print("3. Salir")
        opcion = input("→ ")

        if opcion == "1":
            registrar_usuario()
        elif opcion == "2":
            usuario = iniciar_sesion()
            if usuario:
                if usuario['tipo'] == "admin":
                    menu_admin(usuario)
                elif usuario['tipo'] == "docente":
                    menu_docente(usuario)
                else:
                    menu_estudiante(usuario)
        elif opcion == "3":
            print("Saliendo del sistema...")
            break

if __name__ == "__main__":
    crear_tablas()
    actualizar_tablas()
    menu_principal()
 