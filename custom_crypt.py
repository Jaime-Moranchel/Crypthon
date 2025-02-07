import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from argon2.low_level import hash_secret_raw, Type
import random

class SectorCrypt:
    """
    Clase para cifrar y descifrar bloques (sectores) usando AES (ECB) reforzado
    con técnicas de reordenamiento (shuffle) y XOR con ruido.
    """
    def __init__(self, password: str, pin: str, derivation_salt: bytes = None):
        self.raw_password = password
        # Convertir el PIN a 16 bytes usando shake_256
        self.pin = pin.encode("utf-8")
        self.pin = hashlib.shake_256(self.pin).digest(16)
        # Si no se proporciona sal de derivación, se usa (como fallback) el resultado del PIN
        if derivation_salt is None:
            derivation_salt = self.pin
        self.derivation_salt = derivation_salt
        self.key = self._derive_key()
        self.aes = AES.new(self.key, AES.MODE_ECB)

    def update_derivation_salt(self, derivation_salt: bytes):
        """Actualiza la sal de derivación y re-deriva la clave."""
        self.derivation_salt = derivation_salt
        self.key = self._derive_key()
        self.aes = AES.new(self.key, AES.MODE_ECB)

    def _derive_key(self) -> bytes:
        """
        Deriva una clave de 32 bytes a partir del password y la sal de derivación,
        usando Argon2 de forma determinista.
        """
        pwd_bytes = self.raw_password.encode("utf-8")
        hash_bytes = hash_secret_raw(
            secret=pwd_bytes,
            salt=self.derivation_salt,
            time_cost=2,
            memory_cost=1024,  # 1 MiB en KiB
            parallelism=2,
            hash_len=32,
            type=Type.ID
        )
        # Aplicar SHA-256 al hash resultante para obtener una clave de 32 bytes
        return hashlib.sha256(hash_bytes).digest()

    def _generate_seed(self, sector_number: int) -> int:
        """Genera una semilla determinística a partir de la clave, el número de sector y el PIN."""
        combined = self.key + sector_number.to_bytes(4, "big") + self.pin
        return int.from_bytes(hashlib.sha256(combined).digest(), "big")

    def encrypt_sector(self, sector_number: int, data: bytes) -> bytes:
        """Cifra un sector: pad → AES → shuffle → XOR con ruido."""
        if len(data) % AES.block_size != 0:
            data = pad(data, AES.block_size)
        encrypted = self.aes.encrypt(data)
        seed = self._generate_seed(sector_number)
        shuffled = self._shuffle_bytes(encrypted, seed)
        noised = self._apply_noise(shuffled, seed)
        return noised

    def decrypt_sector(self, sector_number: int, data: bytes) -> bytes:
        """Descifra un sector: quitar ruido → deshacer shuffle → AES → unpad."""
        seed = self._generate_seed(sector_number)
        unnoised = self._apply_noise(data, seed)  # La operación XOR es reversible
        unshuffled = self._shuffle_bytes(unnoised, seed, reverse=True)
        decrypted = self.aes.decrypt(unshuffled)
        try:
            decrypted = unpad(decrypted, AES.block_size)
        except ValueError:
            # Si falla el unpad, se devuelven los datos tal cual
            pass
        return decrypted

    def _shuffle_bytes(self, data: bytes, seed: int, reverse: bool = False) -> bytes:
        data_array = list(data)
        indices = list(range(len(data_array)))
        rng = random.Random(seed)
        rng.shuffle(indices)
        if reverse:
            unshuffled = [None] * len(data_array)
            for original_idx, shuffled_idx in enumerate(indices):
                unshuffled[shuffled_idx] = data_array[original_idx]
            return bytes(unshuffled)
        else:
            shuffled = [None] * len(data_array)
            for i, idx in enumerate(indices):
                shuffled[i] = data_array[idx]
            return bytes(shuffled)

    def _apply_noise(self, data: bytes, seed: int) -> bytes:
        rng = random.Random(seed)
        noise = bytes(rng.getrandbits(8) for _ in range(len(data)))
        return bytes(b ^ n for b, n in zip(data, noise))
