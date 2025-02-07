# Documentación Técnica Detallada del Proyecto Crypthon

## 1. Introducción

Crypthon es un sistema de archivos virtual cifrado inspirado en VeraCrypt. Su objetivo es proporcionar una capa de seguridad y flexibilidad en el almacenamiento de datos. Este documento describe en profundidad su arquitectura, funcionamiento y componentes clave.

## 2. Estructura del Proyecto

El proyecto consta de los siguientes módulos principales:

- `main.py`: Interfaz de línea de comandos para interactuar con el sistema de archivos.
- `fs.py`: Implementación del sistema de archivos virtual.
- `custom_crypt.py`: Módulo de cifrado basado en AES y técnicas adicionales de seguridad.
- `utils.py`: Funciones auxiliares para manejo de datos y conversiones.

## 3. Funcionamiento General

El sistema de archivos funciona sobre un archivo binario (`virtual_disk.img`), que simula un disco real. Los datos se almacenan en bloques de 4096 bytes y se gestionan mediante inodos y mapas de bits.

### 3.1 Flujo de Operaciones

1. **Inicialización**: El usuario proporciona una contraseña y un PIN para derivar la clave de cifrado.
2. **Montaje del sistema de archivos**: Se carga el `virtual_disk.img`, verificando su estructura.
3. **Manipulación de archivos**: Operaciones de creación, lectura, escritura y eliminación se ejecutan sobre el sistema de archivos virtual.
4. **Cifrado y descifrado**: Los datos se cifran antes de almacenarse y se descifran al recuperarse.

## 4. Detalles del Sistema de Archivos

### 4.1 Formato del Disco Virtual

El archivo `virtual_disk.img` sigue la siguiente estructura:

| Bloque      | Contenido                                                      |
| ----------- | -------------------------------------------------------------- |
| 0           | Superbloque (metadatos del sistema de archivos)                |
| 1 - N       | Bloques de mapa de bits (gestión de bloques libres y ocupados) |
| N+1 - M     | Bloques de inodos (almacenamiento de metadatos de archivos)    |
| M+1 - Final | Bloques de datos (contenido real de archivos)                  |

#### Explicación

- **Superbloque (Bloque 0)**: Contiene metadatos críticos del sistema de archivos, como el identificador del sistema, la cantidad de bloques de mapa de bits, de inodos y de datos.
- **Bloques de Mapa de Bits (Bloques 1 - N)**: Gestionan los bloques libres y ocupados del sistema. Cada bit representa un bloque: un `0` indica que el bloque está libre, mientras que un `1` indica que está ocupado. Este enfoque es común en sistemas de archivos como ext4 y NTFS ([Referencia](https://ull-esit-sistemas-operativos.github.io/ssoo-apuntes/so2324/implementaci%C3%B3n_de_sistemas_de_archivos.html)).
- **Bloques de Inodos (Bloques N+1 - M)**: Almacenan los inodos, que son estructuras de datos que contienen información sobre los archivos, como permisos, propietario, tamaño y punteros a los bloques de datos ([Referencia](https://blog.adrianistan.eu/como-funcionan-los-sistemas-basados-en-inodos/)).
- **Bloques de Datos (Bloques M+1 - Final)**: Almacenan el contenido real de los archivos.

Esta estructura permite una gestión eficiente del espacio y facilita operaciones como la creación, lectura y eliminación de archivos.

### 4.2 Superbloque

El bloque 0 almacena información crítica sobre el sistema de archivos:

- **Identificador del sistema**
- **Cantidad de bloques de mapa de bits**
- **Cantidad de bloques de inodos**
- **Cantidad total de bloques de datos**

### 4.3 Inodos

Cada archivo en el sistema se representa con un inodo de 64 bytes:

- Byte 0: Indica si el inodo está en uso.
- Bytes 1-8: Tamaño del archivo en bytes.
- Bytes 9-40: Nombre del archivo.
- Bytes 41-56: Punteros directos a bloques de datos.
- Bytes 57-60: Puntero indirecto a un bloque de punteros.
- Bytes 61-64: Puntero doble indirecto a bloques de punteros.

#### Explicación

Un inodo es una estructura de datos que almacena información sobre un archivo o directorio, excluyendo su nombre y contenido real. Incluye detalles como permisos, propietario, grupo, tamaño, fechas de creación y modificación, y punteros a los bloques de datos donde se almacena el contenido del archivo ([Referencia](https://geekland.eu/inodos-dentires-sistema-archivos/)).

### 4.4 Mapa de Bits

El sistema usa bloques de bits para rastrear los bloques de datos ocupados y libres. Cada bit representa un bloque: `0` indica libre, `1` indica ocupado.

#### Explicación

El mapa de bits es una estructura de datos utilizada para rastrear el estado de los bloques en el sistema de archivos. Este método es eficiente en términos de espacio y permite una rápida verificación del estado de los bloques ([Referencia](https://ull-esit-sistemas-operativos.github.io/ssoo-apuntes/so2324/implementaci%C3%B3n_de_sistemas_de_archivos.html)).

## 5. Seguridad y Cifrado

El cifrado se basa en AES-256 en modo ECB, con una capa adicional de ofuscación:

1. **Derivación de clave**:

   - PIN: `shake_256(pin).digest(16)`
   - Contraseña: `argon2id(password, salt=pin, hash_len=32)`
   - Clave final: `sha256(password_hash)`

2. **Cifrado por bloque**:

   - Cada bloque se cifra con AES-256 ECB.
   - Se aplica una permutación basada en una semilla derivada de la clave y el número de sector.
   - Se inyecta ruido pseudoaleatorio para evitar patrones predecibles.

#### Explicación

- **AES-256 en Modo ECB:** AES es un cifrado simétrico ampliamente adoptado por su robustez y eficiencia. El modo ECB cifra cada bloque de datos de forma independiente, lo que puede ser una desventaja si hay patrones repetitivos en los datos ([Referencia](https://www.kiteworks.com/es/gestion-de-riesgos-de-ciberseguridad/cifrado-aes-256-protege-tus-datos-con-criptografia-de-clave-simetrica/)).
- **Derivación de Clave con Argon2id:** Argon2id es una función de derivación de claves resistente a ataques de fuerza bruta y de canal lateral. Combina las ventajas de Argon2i y Argon2d ([Referencia](https://es.wikipedia.org/wiki/Argon2)).

## 6. Comandos y Uso

#### 6.1. Formatear el disco:
```bash
python3 main.py format --disk <ficher>
```

#### 6.2. Crear un archivo nuevo copiando datos desde un archivo fuente
```bash
python3 main.py create <nombre_fichero> <ruta_origen> --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py create patata README.md --disk imagen_disco.img
```

#### 6.3. Listar archivos:
```bash
python3 main.py list --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py list --disk imagen_disco.img
```

#### 6.4. Leer un fichero
```bash
python3 main.py read <nombre_fichero> --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py read patata --disk imagen_disco.img
```

#### 6.5. Eliminar un fichero:
```bash
python3 main.py delete <nombre_fichero> --disk <archivo_disco_virtual>
```
Ejemplo:
```bash
python3 main.py delete patata --disk imagen_disco.img
```

#### 6.6. Formatear el disco virtual (elimina todos los archivos)
```bash
format
```
**Advertencia:** Esta acción es irreversible.

#### 6.7. Salir del programa
```bash
exit
```

## 7. Conclusión

Este documento proporciona una descripción técnica detallada del funcionamiento interno de Crypthon. Su arquitectura modular y su enfoque en seguridad mediante cifrado fuerte lo convierten en un sistema de archivos virtual robusto y confiable.

