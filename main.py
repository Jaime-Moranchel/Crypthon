#!/usr/bin/env python3
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

    # Inicializar el disco
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
        cmd_input = input("pycrypt> ").strip()
        if not cmd_input:
            continue
        # Separa el comando de los argumentos
        parts = cmd_input.split(" ", 1)
        command = parts[0].lower()  # Solo el comando se pasa a minúsculas
        args_str = parts[1] if len(parts) > 1 else ""
        
        if command == "exit":
            break
        elif command == "list":
            fs.list_files()
        elif command == "create":
            # Se esperan dos argumentos: nombre_archivo y ruta_fuente
            args_parts = args_str.split(" ", 1)
            if len(args_parts) < 2:
                print("Uso: create <nombre_archivo> <ruta_fuente>")
                continue
            filename = args_parts[0]
            source_path = args_parts[1]
            if fs.create_file(filename, source_path):
                print("Archivo creado exitosamente.")
            else:
                print("Error al crear el archivo.")
        elif command == "read":
            if not args_str:
                print("Uso: read <nombre_archivo>")
                continue
            filename = args_str
            data = fs.read_file(filename)
            if data:
                try:
                    print(data.decode('utf-8', errors='replace'))
                except Exception as e:
                    print(f"Error al decodificar el archivo: {e}")
        elif command == "delete":
            if not args_str:
                print("Uso: delete <nombre_archivo>")
                continue
            filename = args_str
            if fs.delete_file(filename):
                print("Archivo borrado.")
            else:
                print("Error al borrar el archivo.")
        elif command == "rename":
            args_parts = args_str.split(" ", 1)
            if len(args_parts) < 2:
                print("Uso: rename <nombre_actual> <nuevo_nombre>")
                continue
            old_name = args_parts[0]
            new_name = args_parts[1]
            if fs.rename_file(old_name, new_name):
                print("Archivo renombrado.")
            else:
                print("Error al renombrar el archivo.")
        elif command == "format":
            confirm = input("¿Está seguro de formatear el disco? Esto borrará todos los datos (yes/no): ")
            if confirm.lower() == "yes":
                fs.format()
        else:
            print("Comandos disponibles: list, create, read, delete, rename, format, exit")

    disk.close()
    print("Saliendo...")

if __name__ == "__main__":
    main()
