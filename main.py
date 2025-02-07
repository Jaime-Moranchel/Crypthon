#!/usr/bin/env python3
# main.py
import argparse
from disk import Disk
from fs import FileSystem
from custom_crypt import SectorCrypt

def main():
    parser = argparse.ArgumentParser(
        description="Sistema de archivos cifrado (PyCrypt Optimizado)"
    )
    parser.add_argument("disk_image", help="Ruta al archivo de imagen de disco (ej. virtual_disk.img)")
    args = parser.parse_args()

    # Inicializar el “disco”
    disk = Disk(args.disk_image, sector_size=512)
    # Solicitar credenciales
    password = input("Ingrese password: ")
    pin = input("Ingrese PIN: ")
    crypt = SectorCrypt(password, pin)
    # Inicializar el sistema de archivos (bloques de 4096 bytes)
    fs = FileSystem(disk, crypt, block_size=4096)

    print("Sistema de archivos inicializado.")
    print("Comandos disponibles: list, create, read, delete, rename, format, exit")
    while True:
        cmd = input("pycrypt> ").strip().lower()
        if cmd == "exit":
            break
        elif cmd == "list":
            fs.list_files()
        elif cmd.startswith("create "):
            parts = cmd.split(" ", 2)
            if len(parts) < 3:
                print("Uso: create <nombre_archivo> <ruta_fuente>")
                continue
            filename = parts[1]
            source_path = parts[2]
            if fs.create_file(filename, source_path):
                print("Archivo creado exitosamente.")
            else:
                print("Error al crear el archivo.")
        elif cmd.startswith("read "):
            parts = cmd.split(" ", 1)
            if len(parts) < 2:
                print("Uso: read <nombre_archivo>")
                continue
            filename = parts[1]
            data = fs.read_file(filename)
            if data:
                try:
                    print(data.decode('utf-8', errors='replace'))
                except Exception as e:
                    print(f"Error al decodificar el archivo: {e}")
        elif cmd.startswith("delete "):
            parts = cmd.split(" ", 1)
            filename = parts[1]
            if fs.delete_file(filename):
                print("Archivo borrado.")
            else:
                print("Error al borrar el archivo.")
        elif cmd.startswith("rename "):
            parts = cmd.split(" ", 2)
            if len(parts) < 3:
                print("Uso: rename <nombre_actual> <nuevo_nombre>")
                continue
            old_name = parts[1]
            new_name = parts[2]
            if fs.rename_file(old_name, new_name):
                print("Archivo renombrado.")
            else:
                print("Error al renombrar el archivo.")
        elif cmd == "format":
            confirm = input("¿Está seguro de formatear el disco? Esto borrará todos los datos (yes/no): ")
            if confirm.lower() == "yes":
                fs.format()
        else:
            print("Comandos disponibles: list, create, read, delete, rename, format, exit")

    disk.close()
    print("Saliendo...")

if __name__ == "__main__":
    main()
