import sqlite3
from datetime import datetime
from base_de_datos import conectar, crear_tablas, actualizar_tablas
import json

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

    print("\n=== SOLICITAR PRÉSTAMO ===")
    print("¿Desea buscar por:")
    print("1. Título de libro")
    print("2. Categoría")
    opcion = input("→ ")

    if opcion == "2":
        # Buscar por categoría
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

            # Determinar estado
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
        # Buscar por título
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
            # Preguntar si quiere reservar
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

    # Solicitar cantidad de préstamo
    try:
        cantidad_deseada = int(input("¿Cuántos ejemplares desea solicitar?: "))
    except ValueError:
        print("Cantidad no válida.")
        conexion.close()
        return

    cursor.execute("SELECT cantidad_disponible, titulo FROM libros WHERE id_libro = ?", (id_libro,))
    libro_info = cursor.fetchone()
    if not libro_info:
        print("Libro no encontrado.")
        conexion.close()
        return

    cantidad_disponible, titulo_libro = libro_info

    if cantidad_deseada > cantidad_disponible:
        print(f"Solo hay {cantidad_disponible} ejemplares disponibles de '{titulo_libro}'.")
        conexion.close()
        return

    try:
        # Registrar préstamo
        cursor.execute("""
            INSERT INTO prestamos (id_usuario, id_libro, fecha_prestamo, cantidad_prestada, estado)
            VALUES (?, ?, date('now'), ?, 'pendiente')
        """, (usuario['id'], id_libro, cantidad_deseada))

        # Actualizar cantidad disponible
        cursor.execute("""
            UPDATE libros
            SET cantidad_disponible = cantidad_disponible - ?
            WHERE id_libro = ?
        """, (cantidad_deseada, id_libro))

        # ===== ACTUALIZAR ESTADO DEL LIBRO =====
        cursor.execute("SELECT cantidad_disponible, cantidad_reservada FROM libros WHERE id_libro = ?", (id_libro,))
        cantidad_final, cantidad_reservada = cursor.fetchone()

        if cantidad_final == 0 and cantidad_reservada > 0:
            nuevo_estado = "reservado"
        elif cantidad_final == 0:
            nuevo_estado = "prestado"
        else:
            nuevo_estado = "disponible"

        cursor.execute("UPDATE libros SET estado = ? WHERE id_libro = ?", (nuevo_estado, id_libro))
        
        conexion.commit()
        print(f"Se ha registrado la solicitud de {cantidad_deseada} ejemplar(es) de '{titulo_libro}'.")

    except sqlite3.Error as e:
        print(f"Error al registrar el préstamo: {e}")
    finally:
        conexion.close()



# === Ver estado de préstamos ===
def ver_prestamos_usuario(usuario):
    """
    Muestra todos los préstamos del usuario (pendientes, aprobados, etc.)
    """
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT p.id, l.titulo, p.fecha_prestamo, p.estado
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.id_usuario = ?
        ORDER BY p.fecha_prestamo DESC
    """, (usuario['id'],))

    prestamos = cursor.fetchall()
    conexion.close()

    if not prestamos:
        print("\nNo tienes préstamos registrados.")
        return

    print("\n=== TUS PRÉSTAMOS ===")
    for prestamo in prestamos:
        id_prestamo, titulo, fecha, estado = prestamo
        print(f"ID: {id_prestamo} | Libro: {titulo} | Fecha: {fecha} | Estado: {estado}")

# === Aprobación de préstamos ===
def aprobar_prestamos():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, u.nombre, l.titulo, p.estado
        FROM prestamos p
        JOIN usuarios u ON p.id_usuario = u.id
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.estado = 'pendiente'
    """)

    prestamos = cur.fetchall()

    if not prestamos:
        print("No hay solicitudes pendientes.")
    else:
        for p in prestamos:
            print(f"ID Préstamo: {p[0]} | Usuario: {p[1]} | Libro: {p[2]} | Estado: {p[3]}")

            decision = input("¿Aprobar este préstamo? (s/n): ").lower()
            if decision == "s":
                cur.execute("UPDATE prestamos SET estado = 'aprobado' WHERE id = ?", (p[0],))
                print("Préstamo aprobado.")
            else:
                cur.execute("UPDATE prestamos SET estado = 'rechazado' WHERE id = ?", (p[0],))

                cur.execute("""
                    UPDATE libros
                    SET cantidad_disponible = cantidad_disponible + 1,
                        estado = CASE 
                                   WHEN (cantidad_disponible + 1) > 0 THEN 'Disponible'
                                   ELSE estado
                                 END
                    WHERE id_libro = (SELECT id_libro FROM prestamos WHERE id = ?)
                """, (p[0],))

                print("Préstamo rechazado.")

    conn.commit()
    conn.close()

# === Menús según usuario===
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
        print("11. Cerrar sesión")
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
            break

def menu_docente(usuario):
    while True:
        print("\n=== MENÚ DEL DOCENTE ===")
        print("1. Buscar libros")
        print("2. Ver libros por categoría")
        print("3. Solicitar préstamo")
        print("4. Ver mis préstamos")
        print("5. Cerrar sesión")
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
        print("5. Cerrar sesión")
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
 