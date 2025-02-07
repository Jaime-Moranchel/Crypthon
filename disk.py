import os

class Disk:
    """
    Clase que simula un disco RAW usando un archivo de imagen.
    Se asume que la imagen existe y tiene un tamaño fijo.
    """
    def __init__(self, disk_path: str, sector_size: int = 512):
        self.disk_path = disk_path
        self.sector_size = sector_size
        self.fd = os.open(self.disk_path, os.O_RDWR)
        self.disk_size = os.path.getsize(self.disk_path)
        self.num_sectors = self.disk_size // self.sector_size

    def read_sector(self, sector_number: int, size: int = None) -> bytes:
        """Lee un sector (o varios) desde el disco."""
        if size is None:
            size = self.sector_size
        if size % self.sector_size != 0:
            raise ValueError(f"El tamaño a leer debe ser múltiplo de {self.sector_size} bytes")
        offset = sector_number * self.sector_size
        os.lseek(self.fd, offset, os.SEEK_SET)
        return os.read(self.fd, size)

    def write_sector(self, sector_number: int, data: bytes) -> None:
        """Escribe datos en un sector (o bloques consecutivos)."""
        if len(data) % self.sector_size != 0:
            raise ValueError(f"La longitud de los datos debe ser múltiplo de {self.sector_size} bytes")
        offset = sector_number * self.sector_size
        os.lseek(self.fd, offset, os.SEEK_SET)
        os.write(self.fd, data)

    def close(self):
        """Cierra el descriptor del disco."""
        os.close(self.fd)
