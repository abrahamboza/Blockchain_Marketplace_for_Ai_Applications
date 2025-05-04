from Blockchain.blockchain import Blockchain, Block
from database import DatabaseManager, User, DataEntry, ModelEntry, EncryptedFile
from encryption import generate_key, encrypt_file, decrypt_file, hash_key
import json
import hashlib
import time
from database import BlockEntry
import uuid


class MarketplaceBlockchain(Blockchain):
    def __init__(self, db_manager=None):
        """Initialisiert die Blockchain mit Datenbankanbindung"""
        super().__init__()

        # Datenbankmanager erstellen, falls keiner übergeben wurde
        self.db_manager = db_manager or DatabaseManager()

    def register_user(self, address, public_key=None):
        """Registriert einen neuen Benutzer in der Datenbank

        Args:
            address: Blockchain-Adresse des Benutzers
            public_key: Öffentlicher Schlüssel (optional)

        Returns:
            User: Neu erstellter Benutzer
        """
        session = self.db_manager.get_session()
        try:
            user = session.query(User).filter_by(address=address).first()
            if user:
                if public_key and not user.public_key:
                    user.public_key = public_key
                    session.commit()
                return user

            # Neuen Benutzer erstellen
            new_user = User(address=address, public_key=public_key)
            session.add(new_user)
            session.commit()
            return new_user
        finally:
            session.close()

    def upload_data_with_file(self, owner_address, file_content, metadata, price):
        """Lädt Daten mit einer Datei hoch und verschlüsselt sie

        Args:
            owner_address: Adresse des Besitzers
            file_content: Dateiinhalt (Bytes oder String)
            metadata: Metadaten-Dictionary
            price: Preis der Daten

        Returns:
            tuple: (data_id, encryption_key)
        """
        session = self.db_manager.get_session()
        try:
            # Benutzer finden oder erstellen
            user = self.register_user(owner_address)

            # Datei verschlüsseln
            key = generate_key()
            encrypted_content = encrypt_file(file_content, key)
            key_hash = hash_key(key)

            # Blockchain-Transaktion erstellen
            metadata_with_hash = metadata.copy()

            # Erstelle einen eindeutigen Hash durch Hinzufügen von Timestamp und Benutzer-ID
            unique_data = (str(file_content) + str(time.time()) + str(user.id)).encode()
            file_hash = hashlib.sha256(unique_data).hexdigest()
            metadata_with_hash['file_hash'] = file_hash

            # Transaktion zur Blockchain hinzufügen
            data_id = self.data_upload_transaction(owner_address, metadata_with_hash, price)

            # Eintrag in der Datenbank erstellen
            data_entry = DataEntry(
                data_id=data_id,
                owner_id=user.id,
                data_metadata=json.dumps(metadata),  # Geändert von metadata
                price=price,
                timestamp=time.time()
            )

            session.add(data_entry)
            session.flush()  # ID generieren

            # Verschlüsselte Datei in der Datenbank speichern
            encrypted_file = EncryptedFile(
                file_hash=file_hash,
                encrypted_content=encrypted_content,
                encryption_key_hash=key_hash,
                data_entry_id=data_entry.id
            )
            session.add(encrypted_file)
            session.commit()

            return data_id, key.decode()  # Schlüssel als String zurückgeben
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def upload_model_with_file(self, owner_address, file_content, metadata, price):
        """Lädt ein Modell mit einer Datei hoch und verschlüsselt es

        Args:
            owner_address: Adresse des Besitzers
            file_content: Dateiinhalt (Bytes oder String)
            metadata: Metadaten-Dictionary
            price: Preis des Modells

        Returns:
            tuple: (model_id, encryption_key)
        """
        session = self.db_manager.get_session()
        try:
            # Benutzer finden oder erstellen
            user = self.register_user(owner_address)

            # Datei verschlüsseln
            key = generate_key()
            encrypted_content = encrypt_file(file_content, key)
            key_hash = hash_key(key)

            # Blockchain-Transaktion erstellen
            metadata_with_hash = metadata.copy()
            metadata_with_hash['file_hash'] = hashlib.sha256(file_content if isinstance(file_content, bytes)
                                                             else file_content.encode()).hexdigest()

            # Transaktion zur Blockchain hinzufügen
            model_id = self.model_upload_transaction(owner_address, metadata_with_hash, price)

            # Eintrag in der Datenbank erstellen
            model_entry = ModelEntry(
                model_id=model_id,
                owner_id=user.id,
                model_metadata=json.dumps(metadata),  # Geändert von metadata
                price=price,
                timestamp=time.time()
            )
            session.add(model_entry)
            session.flush()  # ID generieren

            # Verschlüsselte Datei in der Datenbank speichern
            encrypted_file = EncryptedFile(
                file_hash=metadata_with_hash['file_hash'],
                encrypted_content=encrypted_content,
                encryption_key_hash=key_hash,
                model_entry_id=model_entry.id
            )
            session.add(encrypted_file)
            session.commit()

            return model_id, key.decode()  # Schlüssel als String zurückgeben
        finally:
            session.close()

    def purchase_data(self, buyer_address, data_id, amount):
        """Kauft Daten und gibt den Entschlüsselungsschlüssel zurück

        Args:
            buyer_address: Adresse des Käufers
            data_id: ID der zu kaufenden Daten
            amount: Zu zahlender Betrag

        Returns:
            str: Entschlüsselungsschlüssel
        """
        session = self.db_manager.get_session()
        try:
            # Benutzer finden oder erstellen
            user = self.register_user(buyer_address)

            # Daten finden
            data_entry = session.query(DataEntry).filter_by(data_id=data_id).first()
            if not data_entry:
                raise ValueError(f"Daten mit ID {data_id} nicht gefunden")

            # Transaktion durchführen
            self.data_purchase_transaction(buyer_address, data_id, amount)

            # Beziehung aktualisieren
            if user not in data_entry.purchased_by:
                data_entry.purchased_by.append(user)

            session.commit()

            # Der Schlüssel würde in einer realen Anwendung hier sicher übertragen,
            # z.B. durch asymmetrische Verschlüsselung mit dem öffentlichen Schlüssel des Käufers
            # Hier wird er einfach zurückgegeben

            # In einer Produktionsumgebung würde man hier die Transaktion bestätigen müssen,
            # bevor der Schlüssel übergeben wird
            return "SAMPLE_KEY_TRANSFER"  # Platzhalter
        finally:
            session.close()

    def purchase_model(self, buyer_address, model_id, amount):
        """Kauft ein Modell und gibt den Entschlüsselungsschlüssel zurück

        Args:
            buyer_address: Adresse des Käufers
            model_id: ID des zu kaufenden Modells
            amount: Zu zahlender Betrag

        Returns:
            str: Entschlüsselungsschlüssel
        """
        session = self.db_manager.get_session()
        try:
            # Benutzer finden oder erstellen
            user = self.register_user(buyer_address)

            # Modell finden
            model_entry = session.query(ModelEntry).filter_by(model_id=model_id).first()
            if not model_entry:
                raise ValueError(f"Modell mit ID {model_id} nicht gefunden")

            # Transaktion durchführen
            self.model_purchase_transaction(buyer_address, model_id, amount)

            # Beziehung aktualisieren
            if user not in model_entry.purchased_by:
                model_entry.purchased_by.append(user)

            session.commit()

            # Der Schlüssel würde in einer realen Anwendung hier sicher übertragen werden
            return "SAMPLE_KEY_TRANSFER"  # Platzhalter
        finally:
            session.close()

    def get_data_file(self, user_address, data_id, encryption_key):
        """Gibt die entschlüsselte Datei zurück, wenn der Benutzer Zugriff hat

        Args:
            user_address: Adresse des Benutzers
            data_id: ID der Daten
            encryption_key: Entschlüsselungsschlüssel

        Returns:
            bytes: Entschlüsselte Datei
        """
        session = self.db_manager.get_session()
        try:
            # Benutzer finden
            user = session.query(User).filter_by(address=user_address).first()
            if not user:
                raise ValueError(f"Benutzer mit Adresse {user_address} nicht gefunden")

            # Daten finden
            data_entry = session.query(DataEntry).filter_by(data_id=data_id).first()
            if not data_entry:
                raise ValueError(f"Daten mit ID {data_id} nicht gefunden")

            # Überprüfen, ob der Benutzer Zugriff hat
            if data_entry.owner_id != user.id and user not in data_entry.purchased_by:
                raise ValueError("Kein Zugriff auf diese Daten")

            # Verschlüsselte Datei holen
            encrypted_file = data_entry.encrypted_file
            if not encrypted_file:
                raise ValueError("Keine Datei für diese Daten gefunden")

            # Datei entschlüsseln
            try:
                key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                decrypted_content = decrypt_file(encrypted_file.encrypted_content, key)
                return decrypted_content
            except Exception as e:
                raise ValueError(f"Entschlüsselung fehlgeschlagen: {str(e)}")

        finally:
            session.close()

    def make_block(self, proof: int) -> Block:
        """
        Creates a new Block in the Blockchain
        :param proof:
        :return: new Block
        """
        previous_block = self.last_block

        # Neuen Block erstellen
        block = Block(
            index=len(self.chain),
            previous_hash=previous_block.hash,
            timestamp=time.time(),
            transactions=self.current_transactions,
            proof=proof,
        )

        # Reset current transactions
        self.current_transactions = []

        # Add Block to the chain
        self.chain.append(block)

        # Speichere den Block in der Datenbank
        try:
            self._save_block_to_database(block)
        except Exception as e:
            print(f"Fehler beim Speichern des Blocks in der Datenbank: {e}")

        return block

    def _save_block_to_database(self, block: Block) -> None:
        """
        Speichert einen Block in der Datenbank
        :param block: Der zu speichernde Block
        """
        session = self.db_manager.get_session()
        try:
            # Prüfen, ob Block bereits existiert
            existing_block = session.query(BlockEntry).filter_by(index=block.index).first()
            if existing_block:
                # Block existiert bereits, update
                existing_block.previous_hash = block.previous_hash
                existing_block.timestamp = block.timestamp
                existing_block.proof = block.proof
                existing_block.block_hash = block.hash
                existing_block.transactions_json = json.dumps(block.transactions)
            else:
                # Block neu anlegen
                block_entry = BlockEntry(
                    index=block.index,
                    previous_hash=block.previous_hash,
                    timestamp=block.timestamp,
                    proof=block.proof,
                    block_hash=block.hash,
                    transactions_json=json.dumps(block.transactions)
                )
                session.add(block_entry)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()