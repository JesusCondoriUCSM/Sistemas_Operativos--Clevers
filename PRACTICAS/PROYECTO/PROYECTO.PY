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
    


def cmd_touch(nombre, gpwd):
    """Crea un archivo vacío en el directorio actual."""
    


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

        else:
            print(f"Comando '{cmd}' no reconocido.")


if __name__ == "__main__":
    main()