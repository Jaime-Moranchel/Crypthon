import os
import hashlib
from disk import Disk
from custom_crypt import SectorCrypt

class FileSystem:
    MAGIC_NUMBER = b"SFSE"
    INODE_SIZE = 64  # Cada inodo ocupa 64 bytes

    class Inode:
        def __init__(self, valid: bool, size: int, name: str, direct: list, indirect: int, double_indirect: int, position: int):
            self.valid = valid
            self.size = size
            self.name = name
            self.direct = direct      # Lista de 4 punteros a bloques
            self.indirect = indirect
            self.double_indirect = double_indirect
            self.position = position  # Posición del inodo dentro del área de inodos

        def to_bytes(self) -> bytes:
            data = b'\x01' if self.valid else b'\x00'
            data += self.size.to_bytes(7, 'big')
            name_bytes = self.name.encode('utf-8')[:32]
            name_bytes = name_bytes.ljust(32, b'\x00')
            data += name_bytes
            for ptr in self.direct:
                data += ptr.to_bytes(4, 'big')
            data += self.indirect.to_bytes(4, 'big')
            data += self.double_indirect.to_bytes(4, 'big')
            return data

        @staticmethod
        def from_bytes(data: bytes, position: int) -> 'FileSystem.Inode':
            # Se asume que el inodo fue descifrado correctamente
            valid = (data[0] == 1)
            size = int.from_bytes(data[1:8], 'big')
            name = data[8:40].decode('utf-8').strip('\x00')
            direct = [int.from_bytes(data[i:i+4], 'big') for i in range(40, 56, 4)]
            indirect = int.from_bytes(data[56:60], 'big')
            double_indirect = int.from_bytes(data[60:64], 'big')
            return FileSystem.Inode(valid, size, name, direct, indirect, double_indirect, position)

    def __init__(self, disk: Disk, crypt: SectorCrypt, block_size: int = 4096):
        self.disk = disk
        self.crypt = crypt
        self.block_size = block_size
        # Cálculo de bloques totales e índices internos
        self.total_blocks = self.disk.disk_size // self.block_size
        self.num_inode_blocks = max(1, self.total_blocks // 10000)
        data_blocks = self.total_blocks - 1 - self.num_inode_blocks
        self.num_bitmap_blocks = (data_blocks + self.block_size * 8 - 1) // (self.block_size * 8)
        # Bloques reservados: superblock + bitmap + inodos
        self.offset_data = 1 + self.num_bitmap_blocks + self.num_inode_blocks
        self.directory = {}  # Diccionario: nombre de archivo -> Inodo
        self._init_filesystem()

    def _read_block(self, block_number: int) -> bytes:
        sectors_per_block = self.block_size // self.disk.sector_size
        raw_data = self.disk.read_sector(block_number * sectors_per_block, self.block_size)
        if block_number == 0:
            # El superblock se almacena en claro
            return raw_data
        else:
            return self.crypt.decrypt_sector(block_number, raw_data)

    def _write_block(self, block_number: int, data: bytes) -> None:
        if len(data) != self.block_size:
            data = data.ljust(self.block_size, b'\x00')
        sectors_per_block = self.block_size // self.disk.sector_size
        if block_number == 0:
            # El superblock se almacena en claro
            self.disk.write_sector(block_number * sectors_per_block, data)
        else:
            enc_data = self.crypt.encrypt_sector(block_number, data)
            self.disk.write_sector(block_number * sectors_per_block, enc_data)

    def _init_filesystem(self, force: bool = False):
        superblock_data = self._read_block(0)
        if not force and superblock_data[:4] == self.MAGIC_NUMBER:
            # Si ya existe, se extrae la sal y el hash de la clave derivada,
            # se actualiza el objeto de cifrado y se verifica la integridad de la clave.
            derivation_salt = superblock_data[16:32]
            expected_key_hash = superblock_data[32:64]
            self.crypt.update_derivation_salt(derivation_salt)
            actual_key_hash = hashlib.sha256(self.crypt.key).digest()
            if actual_key_hash != expected_key_hash:
                raise Exception("Credenciales incorrectas. La clave derivada no coincide.")
            self.directory = self._load_inodes()
        else:
            # Formateo: se genera una nueva sal, se actualiza el cifrado y se escribe el superblock.
            derivation_salt = os.urandom(16)
            self.crypt.update_derivation_salt(derivation_salt)
            key_hash = hashlib.sha256(self.crypt.key).digest()
            sb = self.MAGIC_NUMBER
            sb += self.num_bitmap_blocks.to_bytes(4, 'big')
            sb += self.num_inode_blocks.to_bytes(4, 'big')
            sb += (0).to_bytes(4, 'big')  # Cantidad de archivos (inicialmente 0)
            sb += derivation_salt      # Se almacena la sal de derivación
            sb += key_hash             # Se almacena el hash de la clave derivada
            sb = sb.ljust(self.block_size, b'\x00')
            self._write_block(0, sb)
            # Inicializar a cero los bloques de bitmap e inodos
            for blk in range(1, self.offset_data):
                self._write_block(blk, b'\x00' * self.block_size)
            self.directory = {}
            print("Disco formateado con nueva sal de derivación.")

    def _load_inodes(self) -> dict:
        directory = {}
        start_block = 1 + self.num_bitmap_blocks
        inodes_per_block = self.block_size // self.INODE_SIZE
        for blk in range(start_block, start_block + self.num_inode_blocks):
            block_data = self._read_block(blk)
            for i in range(inodes_per_block):
                offset = i * self.INODE_SIZE
                inode_data = block_data[offset:offset + self.INODE_SIZE]
                inode = FileSystem.Inode.from_bytes(inode_data, (blk - start_block) * inodes_per_block + i)
                if inode.valid:
                    directory[inode.name] = inode
        return directory

    def _write_inode(self, inode: 'FileSystem.Inode') -> None:
        start_block = 1 + self.num_bitmap_blocks
        inodes_per_block = self.block_size // self.INODE_SIZE
        blk = start_block + (inode.position // inodes_per_block)
        index = inode.position % inodes_per_block
        block_data = bytearray(self._read_block(blk))
        offset = index * self.INODE_SIZE
        block_data[offset:offset + self.INODE_SIZE] = inode.to_bytes()
        self._write_block(blk, bytes(block_data))

    def _find_free_inode_position(self) -> int:
        start_block = 1 + self.num_bitmap_blocks
        inodes_per_block = self.block_size // self.INODE_SIZE
        total_inodes = self.num_inode_blocks * inodes_per_block
        for pos in range(total_inodes):
            blk = start_block + (pos // inodes_per_block)
            index = pos % inodes_per_block
            block_data = self._read_block(blk)
            offset = index * self.INODE_SIZE
            if block_data[offset] != 1:  # Inodo no válido
                return pos
        raise Exception("No hay inodo libre disponible.")

    def _set_bitmap(self, block_number: int, used: bool):
        relative = block_number - self.offset_data
        if relative < 0:
            return  # No es un bloque de datos
        bit_index = relative
        byte_index = bit_index // 8
        bit_in_byte = bit_index % 8
        bitmap_block_num = 1 + (byte_index // self.block_size)
        bitmap_data = bytearray(self._read_block(bitmap_block_num))
        offset = byte_index % self.block_size
        if used:
            bitmap_data[offset] |= (1 << bit_in_byte)
        else:
            bitmap_data[offset] &= ~(1 << bit_in_byte)
        self._write_block(bitmap_block_num, bytes(bitmap_data))

    def _find_free_block(self) -> int:
        for block in range(self.offset_data, self.total_blocks):
            relative = block - self.offset_data
            byte_index = relative // 8
            bit_in_byte = relative % 8
            bitmap_block_num = 1 + (byte_index // self.block_size)
            bitmap_data = self._read_block(bitmap_block_num)
            bitmap_byte = bitmap_data[byte_index % self.block_size]
            if not (bitmap_byte & (1 << bit_in_byte)):
                self._set_bitmap(block, True)
                return block
        raise Exception("No se encontró bloque libre.")

    # --- Operaciones sobre archivos ---
    def create_file(self, filename: str, source_path: str) -> bool:
        if filename in self.directory:
            print("El archivo ya existe.")
            return False
        try:
            file_size = os.path.getsize(source_path)
        except Exception as e:
            print(f"Error al obtener el tamaño del archivo: {e}")
            return False
        inode_pos = self._find_free_inode_position()
        inode = FileSystem.Inode(valid=True, size=file_size, name=filename,
                                  direct=[0, 0, 0, 0], indirect=0, double_indirect=0,
                                  position=inode_pos)
        with open(source_path, 'rb') as f:
            for i in range(4):
                chunk = f.read(self.block_size)
                if not chunk:
                    break
                free_block = self._find_free_block()
                inode.direct[i] = free_block
                self._write_block(free_block, chunk)
            if f.read(1):
                print("El archivo es demasiado grande. Se soporta máximo 4 bloques directos.")
                return False
        self._write_inode(inode)
        self.directory[filename] = inode
        return True

    def read_file(self, filename: str) -> bytes:
        if filename not in self.directory:
            print("Archivo no encontrado.")
            return b""
        inode = self.directory[filename]
        data = b""
        for blk in inode.direct:
            if blk == 0:
                break
            data += self._read_block(blk)
        return data[:inode.size]

    def delete_file(self, filename: str) -> bool:
        if filename not in self.directory:
            print("Archivo no encontrado.")
            return False
        inode = self.directory[filename]
        for blk in inode.direct:
            if blk != 0:
                self._set_bitmap(blk, False)
        inode.valid = False
        self._write_inode(inode)
        del self.directory[filename]
        return True

    def rename_file(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.directory:
            print("Archivo no encontrado.")
            return False
        if new_name in self.directory:
            print("El nuevo nombre ya existe.")
            return False
        inode = self.directory[old_name]
        inode.name = new_name
        self._write_inode(inode)
        self.directory[new_name] = inode
        del self.directory[old_name]
        return True

    def list_files(self):
        if not self.directory:
            print("No hay archivos en el sistema.")
        for name, inode in self.directory.items():
            print(f"{name} - {inode.size} bytes")

    def format(self):
        self._init_filesystem(force=True)
        print("Disco formateado.")
