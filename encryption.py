from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


def generate_key():
    """Generiert einen neuen Verschlüsselungsschlüssel"""
    return Fernet.generate_key()


def encrypt_file(file_content, key):
    """Verschlüsselt eine Datei mit dem gegebenen Schlüssel

    Args:
        file_content: Inhalt der Datei als Bytes
        key: Fernet-Schlüssel zum Verschlüsseln

    Returns:
        tuple: (verschlüsselte_datei, schlüssel)
    """
    if not isinstance(file_content, bytes):
        file_content = file_content.encode()

    f = Fernet(key)
    encrypted_content = f.encrypt(file_content)
    return encrypted_content


def decrypt_file(encrypted_content, key):
    """Entschlüsselt eine Datei mit dem gegebenen Schlüssel

    Args:
        encrypted_content: Verschlüsselter Inhalt als Bytes
        key: Fernet-Schlüssel zum Entschlüsseln

    Returns:
        bytes: Entschlüsselter Inhalt
    """
    f = Fernet(key)
    try:
        decrypted_content = f.decrypt(encrypted_content)
        return decrypted_content
    except Exception as e:
        raise ValueError(f"Entschlüsselung fehlgeschlagen: {str(e)}")


def hash_key(key):
    """Erzeugt einen Hash des Schlüssels für die Speicherung

    Args:
        key: Verschlüsselungsschlüssel

    Returns:
        str: Hash des Schlüssels
    """
    digest = hashes.Hash(hashes.SHA256())
    digest.update(key)
    key_hash = digest.finalize().hex()
    return key_hash