import threading
import os

FAT_DB = "fat_db.txt"
lock = threading.Lock()
GPWD = 0  # Directorio actual

def inicializar_fat():
    """Crea el archivo fat_db.txt con el directorio raíz si no existe."""
    if not os.path.exists(FAT_DB):
        with open(FAT_DB, "w") as f:
            f.write("0|/|DIR|-1|rwx|-\n") #Estructura de los directorios almacenados
        print("Sistema FAT inicializado correctamente.")
    else:
        print("Sistema FAT cargado desde archivo existente.")


def leer_registros():
    """Lee todos los registros del archivo fat_db.txt y los retorna como lista de dicts."""
    registros = []
    with open(FAT_DB, "r") as f:
        for linea in f:
            linea = linea.strip()
            if linea == "":
                continue
            partes = linea.split("|")
            if len(partes) == 6:
                registros.append({
                    "id":       int(partes[0]),
                    "nombre":   partes[1],
                    "tipo":     partes[2],
                    "padre":    int(partes[3]),
                    "permisos": partes[4],
                    "tamanio":  partes[5]
                })
    return registros


def escribir_registros(registros):
    """Escribe la lista de registros completa en fat_db.txt."""
    with open(FAT_DB, "w") as f:
        for r in registros:
            linea = f"{r['id']}|{r['nombre']}|{r['tipo']}|{r['padre']}|{r['permisos']}|{r['tamanio']}\n"
            f.write(linea)


def siguiente_id(registros):
    """Retorna el siguiente ID disponible."""
    if not registros:
        return 0
    return max(r["id"] for r in registros) + 1


# Obtener la ruta actual

def obtener_ruta(gpwd):
    """Construye la ruta actual recorriendo los padres hasta llegar a la raíz."""
    registros = leer_registros()
    ruta = []
    actual = gpwd

    while actual != -1:
        for r in registros:
            if r["id"] == actual:
                if r["nombre"] != "/":
                    ruta.append(r["nombre"])
                actual = r["padre"]
                break

    ruta.reverse()
    return "/" + "/".join(ruta) if ruta else "/"


# COMANDOS

def cmd_mkdir(nombre, gpwd):
    """Crea un nuevo directorio dentro del directorio actual."""
    with lock:
        registros = leer_registros()

        for r in registros:
            if r["nombre"] == nombre and r["padre"] == gpwd and r["tipo"] == "DIR":
                print(f"Error: ya existe un directorio llamado '{nombre}'.")
                return gpwd

        nuevo_id = siguiente_id(registros)
        nuevo_dir = {
            "id":       nuevo_id,
            "nombre":   nombre,
            "tipo":     "DIR",
            "padre":    gpwd,
            "permisos": "rwx",
            "tamanio":  "-"
        }
        registros.append(nuevo_dir)
        escribir_registros(registros)

    print(f"Directorio '{nombre}' creado correctamente.")
    return gpwd


def cmd_cd(nombre, gpwd):
    """Cambia el directorio actual."""
    registros = leer_registros()

    # Subir un nivel
    if nombre == "..":
        for r in registros:
            if r["id"] == gpwd:
                nuevo_gpwd = r["padre"]
                if nuevo_gpwd == -1:
                    print("Ya estás en el directorio raíz.")
                    return gpwd
                ruta = obtener_ruta(nuevo_gpwd)
                print(f"Directorio actual cambiado a: {ruta}")
                return nuevo_gpwd

    # Bajar a subdirectorio
    for r in registros:
        if r["nombre"] == nombre and r["padre"] == gpwd and r["tipo"] == "DIR":
            ruta = obtener_ruta(r["id"])
            print(f"Directorio actual cambiado a: {ruta}")
            return r["id"]

    print(f"Error: directorio '{nombre}' no encontrado.")
    return gpwd


def cmd_touch(nombre, gpwd):
    """Crea un archivo vacío en el directorio actual."""
    with lock:
        registros = leer_registros()

        for r in registros:
            if r["nombre"] == nombre and r["padre"] == gpwd and r["tipo"] == "FILE":
                print(f"Error: ya existe un archivo llamado '{nombre}'.")
                return

        nuevo_id = siguiente_id(registros)
        nuevo_archivo = {
            "id":       nuevo_id,
            "nombre":   nombre,
            "tipo":     "FILE",
            "padre":    gpwd,
            "permisos": "rw-",
            "tamanio":  "0"
        }
        registros.append(nuevo_archivo)
        escribir_registros(registros)

    print(f"Archivo '{nombre}' creado correctamente.")


def cmd_ls(gpwd):
    """Muestra el contenido del directorio actual."""
    registros = leer_registros()
    contenido = [r for r in registros if r["padre"] == gpwd]

    if not contenido:
        print("(directorio vacío)")
    else:
        for r in contenido:
            print(r["nombre"])


def cmd_ls_l(gpwd):
    """Muestra el contenido detallado del directorio actual."""
    registros = leer_registros()
    contenido = [r for r in registros if r["padre"] == gpwd]

    if not contenido:
        print("(directorio vacío)")
    else:
        print(f"{'ID':<5} | {'TIPO':<5} | {'PERMISOS':<8} | {'TAMAÑO':<7} | NOMBRE")
        print("-" * 45)
        for r in contenido:
            print(f"{r['id']:<5} | {r['tipo']:<5} | {r['permisos']:<8} | {r['tamanio']:<7} | {r['nombre']}")


def cmd_chmod(permisos, nombre, gpwd):
    """Cambia los permisos de un archivo o directorio en el directorio actual."""
    with lock:
        registros = leer_registros()

        for r in registros:
            if r["nombre"] == nombre and r["padre"] == gpwd:
                r["permisos"] = permisos
                escribir_registros(registros)
                print(f"Permisos de '{nombre}' cambiados a {permisos}.")
                return

    print(f"Error: '{nombre}' no encontrado.")


def cmd_rm(nombre, gpwd):
    """Elimina un archivo del directorio actual."""
    with lock:
        registros = leer_registros()

        for r in registros:
            if r["nombre"] == nombre and r["padre"] == gpwd and r["tipo"] == "FILE":
                registros.remove(r)
                escribir_registros(registros)
                print(f"Archivo '{nombre}' eliminado correctamente.")
                return

    print(f"Error: archivo '{nombre}' no encontrado.")


def cmd_test_hilos(gpwd):
    """Simula la creación concurrente de archivos usando hilos."""
    print("Iniciando prueba concurrente con hilos...")

    def crear_archivo(numero):
        nombre = f"hilo_{numero}.txt"
        print(f"Hilo {numero} creando archivo {nombre}")
        cmd_touch(nombre, gpwd)

    hilos = []
    for i in range(1, 6):
        t = threading.Thread(target=crear_archivo, args=(i,))
        hilos.append(t)

    for t in hilos:
        t.start()

    for t in hilos:
        t.join()

    print("Todos los hilos finalizaron correctamente.")


# BUCLE PRINCIPAL

def main():
    global GPWD

    inicializar_fat()

    print("=" * 40)
    print("   SIMULADOR FAT EN PYTHON")
    print("=" * 40)
    print(f"Directorio actual: {obtener_ruta(GPWD)}")
    print("\nComandos disponibles:")
    print("  mkdir <nombre_directorio>")
    print("  cd <nombre_directorio>")
    print("  cd ..")
    print("  touch <nombre_archivo>")
    print("  ls")
    print("  ls -l")
    print("  chmod <permisos> <nombre>")
    print("  rm <nombre_archivo>")
    print("  test_hilos")
    print("  exit")
    print()

    while True:
        ruta = obtener_ruta(GPWD)
        comando = input(f"{ruta}> ").strip()

        if comando == "":
            continue

        partes = comando.split()
        cmd = partes[0]

        if cmd == "exit":
            print("Saliendo del simulador FAT...")
            break

        elif cmd == "mkdir":
            if len(partes) < 2:
                print("Uso: mkdir <nombre_directorio>")
            else:
                GPWD = cmd_mkdir(partes[1], GPWD)

        elif cmd == "cd":
            if len(partes) < 2:
                print("Uso: cd <nombre_directorio> | cd ..")
            else:
                GPWD = cmd_cd(partes[1], GPWD)

        elif cmd == "touch":
            if len(partes) < 2:
                print("Uso: touch <nombre_archivo>")
            else:
                cmd_touch(partes[1], GPWD)

        elif cmd == "ls":
            if len(partes) == 2 and partes[1] == "-l":
                cmd_ls_l(GPWD)
            else:
                cmd_ls(GPWD)

        elif cmd == "chmod":
            if len(partes) < 3:
                print("Uso: chmod <permisos> <nombre>")
            else:
                cmd_chmod(partes[1], partes[2], GPWD)

        elif cmd == "rm":
            if len(partes) < 2:
                print("Uso: rm <nombre_archivo>")
            else:
                cmd_rm(partes[1], GPWD)

        elif cmd == "test_hilos":
            cmd_test_hilos(GPWD)

        else:
            print(f"Comando '{cmd}' no reconocido.")


if __name__ == "__main__":
    main()