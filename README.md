# Documentación del Proyecto Crypthon

## Introducción
Crypthon es un sistema de archivos virtual encriptado inspirado en VeraCrypt, desarrollado en Python. Permite almacenar archivos de manera segura utilizando cifrado AES con técnicas adicionales de aleatorización y ruido para mejorar la seguridad. La interacción con el sistema de archivos se realiza a través de una interfaz de línea de comandos (CLI).
Este proyecto ha surjido como presentación a un trabajo para la asignatura de Sistemas Operativos de DAM sobre bloqueo y encriptación de unidades de almacenamiento.

## Características
- Cifrado basado en **AES-ECB** con capas adicionales de **mezcla y ruido**.
- Derivación de claves con **Argon2** y SHA-256.
- Administración de archivos: **crear, leer, eliminar, renombrar**.
- **Formateo seguro** del disco virtual.
- Soporte para un único nivel de archivos (sin directorios).

## Requisitos
Antes de ejecutar Crypthon, asegúrate de tener instaladas las siguientes dependencias:

```bash
pip install pycryptodome argon2-cffi
```

## Uso
El programa se ejecuta desde la línea de comandos con permisos de superusuario:

```bash
dd if=/dev/zero of=virtual_disk.img bs=1M count=500 # Esto crea una imagen de disco vacía de 500 MB
python3 main.py <archivo_disco_virtual> <opciones>
```

### Comandos Disponibles

#### 1. Formatear el disco:
```bash
python3 main.py format --disk <ficher>
```

#### 2. Crear un archivo nuevo copiando datos desde un archivo fuente
```bash
python3 main.py create <nombre_fichero> <ruta_origen> --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py create patata README.md --disk imagen_disco.img
```

#### 3. Listar archivos:
```bash
python3 main.py list --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py list --disk imagen_disco.img
```

#### 4. Leer un fichero
```bash
python3 main.py read <nombre_fichero> --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py read patata --disk imagen_disco.img
```

#### 5. Eliminar un fichero:
```bash
python3 main.py delete <nombre_fichero> --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py delete patata --disk imagen_disco.img
```

#### 6. Formatear el disco virtual (elimina todos los archivos)
```bash
format
```
**Advertencia:** Esta acción es irreversible.

#### 7. Salir del programa
```bash
exit
```

## Autenticación
Crypthon usa un **sistema de autenticación basado en contraseña y PIN**:
- La contraseña se usa junto con el PIN para generar la clave de cifrado.
- Si es la primera vez que se usa el disco, se puede ingresar cualquier PIN.
- Si el disco ya tiene datos almacenados, se debe ingresar el mismo PIN que se usó previamente, de lo contrario, no será posible descifrar la información.

## Arquitectura del Sistema de Archivos

### Organización del Disco Virtual
- **Superbloque (bloque 0)**: Contiene metadatos del sistema de archivos.
- **Mapa de bits**: Indica qué bloques están ocupados.
- **Bloques de inodos**: Almacenan información sobre los archivos.
- **Bloques de datos**: Contienen el contenido real de los archivos.

### Funcionamiento del Cifrado
1. Se genera una clave de 32 bytes usando **Argon2**.
2. La clave se usa con **AES en modo ECB**.
3. Se aplica **mezcla de bytes y ruido aleatorio** para mitigar patrones repetitivos.

## Consideraciones de Seguridad
- **No se pueden recuperar archivos sin la clave correcta.**
- **El PIN y la contraseña deben ser almacenados de forma segura.**
- **El formateo del disco es irreversible.**

## Conclusión
Crypthon es una solución sencilla pero robusta para almacenar archivos de manera segura en un sistema de archivos virtual encriptado. Su implementación en Python lo hace accesible y fácil de modificar o extender según sea necesario.

