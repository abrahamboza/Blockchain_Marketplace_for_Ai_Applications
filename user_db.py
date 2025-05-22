import json
import os
import hashlib
import uuid
from typing import Dict, List, Optional
from datetime import datetime


class UserDatabase:
    """Eine einfache Datenbankklasse zur Verwaltung von Benutzern."""

    def __init__(self, db_file: str = 'users.json'):
        """
        Initialisiert die Benutzerdatenbank.

        :param db_file: Pfad zur JSON-Datei, in der die Benutzer gespeichert werden.
        """
        self.db_file = db_file
        self.users = {}
        self.load_users()

    def load_users(self) -> None:
        """Lädt die Benutzer aus der JSON-Datei."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.users = {}

    def save_users(self) -> None:
        """Speichert die Benutzer in der JSON-Datei."""
        with open(self.db_file, 'w') as f:
            json.dump(self.users, f, indent=4)

    def hash_password(self, password: str) -> str:
        """
        Erzeugt einen sicheren Hash aus dem Passwort.

        :param password: Das zu hashende Passwort.
        :return: Der Passwort-Hash.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str) -> Dict:
        """
        Registriert einen neuen Benutzer.

        :param username: Der Benutzername.
        :param password: Das Passwort.
        :return: Die Benutzerdaten.
        :raises ValueError: Wenn der Benutzername bereits existiert.
        """
        if username in self.users:
            raise ValueError(f"Benutzername '{username}' ist bereits vergeben.")

        # Generiere Blockchain-Adresse (vereinfacht für Demo-Zwecke)
        blockchain_address = str(uuid.uuid4()).replace('-', '')

        user_data = {
            "username": username,
            "password_hash": self.hash_password(password),
            "blockchain_address": blockchain_address,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "datasets": [],
            "models": [],
            "purchased_datasets": [],
            "purchased_models": []
        }

        self.users[username] = user_data
        self.save_users()

        # Kopie ohne Passwort-Hash zurückgeben
        user_copy = user_data.copy()
        user_copy.pop("password_hash")
        return user_copy

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authentifiziert einen Benutzer.

        :param username: Der Benutzername.
        :param password: Das Passwort.
        :return: Die Benutzerdaten ohne Passwort-Hash oder None, wenn die Authentifizierung fehlschlägt.
        """
        if username not in self.users:
            return None

        user_data = self.users[username]
        password_hash = self.hash_password(password)

        if password_hash != user_data["password_hash"]:
            return None

        # Aktualisiere letzten Login-Zeitpunkt
        user_data["last_login"] = datetime.now().isoformat()
        self.save_users()

        # Kopie ohne Passwort-Hash zurückgeben
        user_copy = user_data.copy()
        user_copy.pop("password_hash")
        return user_copy

    def get_user(self, username: str) -> Optional[Dict]:
        """
        Gibt die Daten eines Benutzers zurück.

        :param username: Der Benutzername.
        :return: Die Benutzerdaten ohne Passwort-Hash oder None, wenn der Benutzer nicht existiert.
        """
        if username not in self.users:
            return None

        user_copy = self.users[username].copy()
        user_copy.pop("password_hash")
        return user_copy

    def get_all_users(self) -> List[Dict]:
        """
        Gibt eine Liste aller Benutzer zurück.

        :return: Liste der Benutzerdaten ohne Passwort-Hashes.
        """
        users_list = []
        for username, user_data in self.users.items():
            user_copy = user_data.copy()
            user_copy.pop("password_hash")
            users_list.append(user_copy)

        return users_list

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Ändert das Passwort eines Benutzers.

        :param username: Der Benutzername.
        :param old_password: Das alte Passwort.
        :param new_password: Das neue Passwort.
        :return: True, wenn das Passwort erfolgreich geändert wurde, sonst False.
        """
        if username not in self.users:
            return False

        user_data = self.users[username]
        old_password_hash = self.hash_password(old_password)

        if old_password_hash != user_data["password_hash"]:
            return False

        user_data["password_hash"] = self.hash_password(new_password)
        self.save_users()
        return True

    def add_dataset(self, username: str, dataset_id: str, metadata: Dict) -> bool:
        """
        Fügt einen Datensatz zum Benutzer hinzu.

        :param username: Der Benutzername.
        :param dataset_id: Die ID des Datensatzes.
        :param metadata: Metadaten des Datensatzes.
        :return: True, wenn der Datensatz erfolgreich hinzugefügt wurde, sonst False.
        """
        if username not in self.users:
            return False

        dataset_entry = {
            "id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }

        self.users[username]["datasets"].append(dataset_entry)
        self.save_users()
        return True

    def add_model(self, username: str, model_id: str, metadata: Dict) -> bool:
        """
        Fügt ein Modell zum Benutzer hinzu.

        :param username: Der Benutzername.
        :param model_id: Die ID des Modells.
        :param metadata: Metadaten des Modells.
        :return: True, wenn das Modell erfolgreich hinzugefügt wurde, sonst False.
        """
        if username not in self.users:
            return False

        model_entry = {
            "id": model_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }

        self.users[username]["models"].append(model_entry)
        self.save_users()
        return True

    def add_purchased_dataset(self, username: str, dataset_id: str) -> bool:
        """
        Fügt einen gekauften Datensatz zum Benutzer hinzu.

        :param username: Der Benutzername.
        :param dataset_id: Die ID des gekauften Datensatzes.
        :return: True, wenn der Datensatz erfolgreich hinzugefügt wurde, sonst False.
        """
        if username not in self.users:
            return False

        if dataset_id not in self.users[username]["purchased_datasets"]:
            self.users[username]["purchased_datasets"].append(dataset_id)
            self.save_users()

        return True

    def add_purchased_model(self, username: str, model_id: str) -> bool:
        """
        Fügt ein gekauftes Modell zum Benutzer hinzu.

        :param username: Der Benutzername.
        :param model_id: Die ID des gekauften Modells.
        :return: True, wenn das Modell erfolgreich hinzugefügt wurde, sonst False.
        """
        if username not in self.users:
            return False

        if model_id not in self.users[username]["purchased_models"]:
            self.users[username]["purchased_models"].append(model_id)
            self.save_users()

        return True