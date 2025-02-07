#!/usr/bin/env python3
import argparse
from disk import Disk
from fs import FileSystem
from custom_crypt import SectorCrypt

def main():
    parser = argparse.ArgumentParser(
        description="Sistema de archivos cifrado (PyCrypt Optimizado)"
    )
    parser.add_argument("command", help="Comando a ejecutar (format, create, list, read, delete, rename, exit)")
    parser.add_argument("args", nargs="*", help="Argumentos para el comando")
    parser.add_argument("--disk", default="virtual_disk.img", help="Ruta a la imagen de disco (default: virtual_disk.img)")
    args = parser.parse_args()

    # Se solicitan las credenciales
    password = input("Ingrese password: ")
    pin = input("Ingrese PIN: ")

    # Se abre el disco y se inicializa el sistema de archivos
    disk = Disk(args.disk, sector_size=512)
    crypt = SectorCrypt(password, pin)
    fs = FileSystem(disk, crypt, block_size=4096)

    if args.command == "format":
        fs.format()
    elif args.command == "create":
        if len(args.args) < 2:
            print("Uso: create <nombre_archivo> <ruta/origen.txt>")
        else:
            filename = args.args[0]
            source_path = args.args[1]
            if fs.create_file(filename, source_path):
                print("Archivo creado exitosamente.")
            else:
                print("Error al crear el archivo.")
    elif args.command == "list":
        fs.list_files()
    elif args.command == "read":
        if len(args.args) < 1:
            print("Uso: read <archivo.txt>")
        else:
            filename = args.args[0]
            data = fs.read_file(filename)
            if data:
                try:
                    print(data.decode('utf-8', errors='replace'))
                except Exception as e:
                    print(f"Error al decodificar el archivo: {e}")
    elif args.command == "delete":
        if len(args.args) < 1:
            print("Uso: delete <archivo.txt>")
        else:
            filename = args.args[0]
            if fs.delete_file(filename):
                print("Archivo borrado.")
            else:
                print("Error al borrar el archivo.")
    elif args.command == "rename":
        if len(args.args) < 2:
            print("Uso: rename <archivo.txt> <nuevo_nombre.txt>")
        else:
            old_name = args.args[0]
            new_name = args.args[1]
            if fs.rename_file(old_name, new_name):
                print("Archivo renombrado.")
            else:
                print("Error al renombrar el archivo.")
    elif args.command == "exit":
        print("Saliendo...")
    else:
        print("Comando desconocido. Comandos disponibles: format, create, list, read, delete, rename, exit")
    disk.close()

if __name__ == "__main__":
    main()
