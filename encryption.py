"""
encryption.py

Laboratorio de Cifrado y Manejo de Credenciales

En este módulo deberás implementar:

- Descifrado AES (MODE_EAX)
- Hash de contraseña con salt usando PBKDF2-HMAC-SHA256
- Verificación de contraseña usando el mismo salt

NO modificar la función encrypt_aes().
"""

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
import hmac
import secrets
import base64
import hashlib
# ==========================================================
# AES-GCM (requiere pip install pycryptodome)
# ==========================================================

def encrypt_aes(texto, clave):
    """
    Cifra un texto usando AES en modo EAX.

    Retorna:
        texto_cifrado_hex
        nonce_hex
        tag_hex
    """

    texto_bytes = texto.encode()

    cipher = AES.new(clave, AES.MODE_EAX)

    nonce = cipher.nonce
    texto_cifrado, tag = cipher.encrypt_and_digest(texto_bytes)

    return (
        texto_cifrado.hex(),
        nonce.hex(),
        tag.hex()
    )




def decrypt_aes(texto_cifrado_str, nonce_hex, tag_hex, clave):
    texto_cifrado = bytes.fromhex(texto_cifrado_str)
    nonce = bytes.fromhex(nonce_hex)
    tag = bytes.fromhex(tag_hex)

    cipher = AES.new(clave, AES.MODE_EAX, nonce=nonce)

    texto_descifrado = cipher.decrypt_and_verify(texto_cifrado, tag)

    return texto_descifrado.decode()

# ==========================================================
# PASSWORD HASHING (PBKDF2 - SHA256)
# ==========================================================


DEFAULT_ITERATIONS = 310_000
SALT_BYTES = 16


def hash_password(password: str) -> dict:
    """
    Genera un hash seguro usando PBKDF2-HMAC-SHA256.
    Retorna un diccionario listo para guardar en JSON.
    """
    salt = secrets.token_bytes(SALT_BYTES)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        DEFAULT_ITERATIONS,
        dklen=32
    )

    return {
        "algorithm": "pbkdf2_sha256",
        "iterations": DEFAULT_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(derived_key).decode("ascii")
    }


def verify_password(password: str, stored: dict) -> bool:
    """
    Verifica si una contraseña coincide con el hash almacenado.
    Usa comparación constante.
    """
    salt = base64.b64decode(stored["salt"])
    expected_hash = base64.b64decode(stored["hash"])

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        int(stored["iterations"]),
        dklen=len(expected_hash)
    )

    return hmac.compare_digest(derived_key, expected_hash)



if __name__ == "__main__":

    print("=== PRUEBA AES ===")

    texto = "Hola Mundo"
    clave = get_random_bytes(16)

    texto_cifrado, nonce, tag = encrypt_aes(texto, clave)
    print("Texto plano: ", texto)
    print("Texto cifrado:", texto_cifrado)
    print("Nonce:", nonce)
    print("Tag:", tag)

    # Cuando implementen decrypt_aes, esto debe funcionar
    texto_descifrado = decrypt_aes(texto_cifrado, nonce, tag, clave)
    print("Texto descifrado:", texto_descifrado)


    print("\n=== PRUEBA HASH ===")

    password = "Password123!"

    # Cuando implementen hash_password:
    pwd_data = hash_password(password)
    print("Hash generado:", pwd_data)

    # Cuando implementen verify_password:
    print("Verificación correcta:",
          verify_password("Password123!", pwd_data))