from Blockchain.blockchain import Blockchain, Block
from database import DatabaseManager, User, DataEntry, ModelEntry, EncryptedFile
from encryption import generate_key, encrypt_file, decrypt_file, hash_key
import json
import hashlib
import time
from database import BlockEntry
from simulated_ipfs import SimulatedIPFS
import uuid


class MarketplaceBlockchain(Blockchain):
    def __init__(self, db_manager=None):
        """Initialisiert die Blockchain mit Datenbankanbindung"""
        super().__init__()

        # Datenbankmanager erstellen, falls keiner übergeben wurde
        self.db_manager = db_manager or DatabaseManager()

        # Initialize the IPFS integration
        self.ipfs = SimulatedIPFS()

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

        Verwendet IPFS für die Speicherung des tatsächlichen Inhalts

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

            # Upload encrypted content to IPFS
            metadata_with_hash = metadata.copy()
            unique_data = (str(file_content) + str(time.time()) + str(user.id)).encode()
            file_hash = hashlib.sha256(unique_data).hexdigest()
            metadata_with_hash['file_hash'] = file_hash

            # Store in IPFS and get CID
            ipfs_cid = self.ipfs.add(encrypted_content, {
                "owner": owner_address,
                "file_hash": file_hash,
                "metadata": json.dumps(metadata),
                "encrypted": True
            })
            self.ipfs.pin(ipfs_cid)

            # Add IPFS reference to metadata
            metadata_with_hash['ipfs_cid'] = ipfs_cid

            # Transaktion zur Blockchain hinzufügen
            data_id = self.data_upload_transaction(owner_address, metadata_with_hash, price)

            # Eintrag in der Datenbank erstellen
            data_entry = DataEntry(
                data_id=data_id,
                owner_id=user.id,
                data_metadata=json.dumps(metadata),
                price=price,
                timestamp=time.time()
            )

            session.add(data_entry)
            session.flush()  # ID generieren

            # Verschlüsselte Datei in der Datenbank speichern - now just a reference to IPFS
            encrypted_file = EncryptedFile(
                file_hash=file_hash,
                encryption_key_hash=key_hash,
                ipfs_cid=ipfs_cid,  # Store IPFS CID instead of the actual content
                data_entry_id=data_entry.id
            )
            session.add(encrypted_file)
            session.commit()

            # NEUER CODE: Verschlüsselungsschlüssel speichern
            try:
                import key_manager
                print(f"DEBUG: Speichere Schlüssel für {data_id}")
                result = key_manager.save_key(metadata.get('name', 'Unknown Dataset'), data_id, key.decode())
                print(f"DEBUG: Schlüssel gespeichert: {result}")
            except Exception as e:
                print(f"ERROR beim Speichern des Schlüssels: {e}")

            return data_id, key.decode()  # Schlüssel als String zurückgeben
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def upload_model_with_file(self, owner_address, file_content, metadata, price):
        """Lädt ein Modell mit einer Datei hoch und verschlüsselt es

        Verwendet IPFS für die Speicherung des tatsächlichen Inhalts

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

            # Calculate unique hash for the file
            unique_data = (str(file_content) + str(time.time()) + str(user.id)).encode()
            file_hash = hashlib.sha256(unique_data).hexdigest()

            # Store in IPFS and get CID
            ipfs_cid = self.ipfs.add(encrypted_content, {
                "owner": owner_address,
                "file_hash": file_hash,
                "metadata": json.dumps(metadata),
                "type": "model",
                "encrypted": True
            })
            self.ipfs.pin(ipfs_cid)

            # Prepare metadata for the blockchain
            metadata_with_hash = metadata.copy()
            metadata_with_hash['file_hash'] = file_hash
            metadata_with_hash['ipfs_cid'] = ipfs_cid

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

            # Verschlüsselte Datei in der Datenbank speichern - now just a reference to IPFS
            encrypted_file = EncryptedFile(
                file_hash=file_hash,
                encryption_key_hash=key_hash,
                ipfs_cid=ipfs_cid,  # Store IPFS CID
                model_entry_id=model_entry.id
            )
            session.add(encrypted_file)
            session.commit()

            # NEUER CODE: Verschlüsselungsschlüssel speichern
            try:
                import key_manager
                print(f"DEBUG: Speichere Schlüssel für {model_id}")
                result = key_manager.save_key(metadata.get('name', 'Unknown Model'), model_id, key.decode())
                print(f"DEBUG: Schlüssel gespeichert: {result}")
            except Exception as e:
                print(f"ERROR beim Speichern des Schlüssels: {e}")

            return model_id, key.decode()  # Schlüssel als String zurückgeben
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_model_file(self, user_address, model_id, encryption_key):
        """Gibt die entschlüsselte Modelldatei zurück, wenn der Benutzer Zugriff hat.
        Holt den Inhalt aus IPFS statt direkt aus der Datenbank.
        KORRIGIERT: Prüft Blockchain direkt für Purchase-Berechtigung.

        Args:
            user_address: Adresse des Benutzers
            model_id: ID des Modells
            encryption_key: Entschlüsselungsschlüssel

        Returns:
            bytes: Entschlüsseltes Modell
        """
        session = self.db_manager.get_session()
        try:
            print(f"\n=== GET_MODEL_FILE DEBUG ===")
            print(f"User: {user_address}, Model ID: {model_id}")

            # Benutzer finden
            user = session.query(User).filter_by(address=user_address).first()
            if not user:
                print(f"❌ Benutzer mit Adresse {user_address} nicht in Datenbank gefunden")
                raise ValueError(f"Benutzer mit Adresse {user_address} nicht gefunden")

            print(f"✅ User gefunden: ID {user.id}")

            # Modell finden
            model_entry = session.query(ModelEntry).filter_by(model_id=model_id).first()
            if not model_entry:
                print(f"❌ ModelEntry mit ID {model_id} nicht gefunden")
                raise ValueError(f"Modell mit ID {model_id} nicht gefunden")

            print(f"✅ ModelEntry gefunden: ID {model_entry.id}, Owner ID: {model_entry.owner_id}")

            # NEUE LOGIK: Überprüfen der Zugriffsberechtigung
            has_access = False
            access_reason = ""

            # 1. Prüfe ob User der Owner ist
            if model_entry.owner_id == user.id:
                has_access = True
                access_reason = "User ist Owner"
                print(f"✅ {access_reason}")
            else:
                print(f"⚠️ User ist nicht Owner (Owner ID: {model_entry.owner_id})")

                # 2. Prüfe Blockchain direkt nach Purchase-Transaktionen
                print(f"🔍 Suche in Blockchain nach Purchase-Transaktionen...")

                purchase_found = False
                for block_idx, block in enumerate(self.chain):
                    for tx_idx, tx in enumerate(block.transactions):
                        if (tx.get('type') in ['data_purchase', 'model_purchase']
                                and tx.get('buyer') == user_address):

                            purchased_item_id = tx.get('data_id') or tx.get('model_id')

                            if purchased_item_id == model_id:
                                purchase_found = True
                                access_reason = f"Purchase gefunden in Block {block_idx}, TX {tx_idx}"
                                print(f"✅ {access_reason}")
                                break

                    if purchase_found:
                        break

                if purchase_found:
                    has_access = True
                else:
                    print(f"❌ Keine Purchase-Transaktion gefunden")

                    # 3. Fallback: Prüfe auch ausstehende Transaktionen
                    print(f"🔍 Prüfe ausstehende Transaktionen...")
                    for tx in self.current_transactions:
                        if (tx.get('type') in ['data_purchase', 'model_purchase']
                                and tx.get('buyer') == user_address):

                            purchased_item_id = tx.get('data_id') or tx.get('model_id')

                            if purchased_item_id == model_id:
                                has_access = True
                                access_reason = "Purchase in ausstehenden Transaktionen gefunden"
                                print(f"✅ {access_reason}")
                                break

            # Finale Zugriffsprüfung
            if not has_access:
                print(f"❌ ZUGRIFF VERWEIGERT: Kein Zugriff auf Modell {model_id}")
                raise ValueError("Kein Zugriff auf dieses Modell")

            print(f"✅ ZUGRIFF GEWÄHRT: {access_reason}")

            # Verschlüsselte Datei holen
            encrypted_file = model_entry.encrypted_file
            if not encrypted_file:
                print(f"❌ Keine verschlüsselte Datei gefunden")
                raise ValueError("Keine Datei für dieses Modell gefunden")

            print(f"✅ Verschlüsselte Datei gefunden")

            # Get the IPFS CID from metadata or the encrypted_file record
            ipfs_cid = None
            metadata = json.loads(model_entry.model_metadata) if model_entry.model_metadata else {}
            ipfs_cid = metadata.get("ipfs_cid") or encrypted_file.ipfs_cid

            if not ipfs_cid:
                # Fallback zu direktem Inhalt falls kein IPFS CID (für Rückwärtskompatibilität)
                if encrypted_file.encrypted_content:
                    print(f"⚠️ Verwende direkten DB-Inhalt (kein IPFS)")
                    try:
                        key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                        decrypted_content = decrypt_file(encrypted_file.encrypted_content, key)
                        print(f"✅ Direkte Entschlüsselung erfolgreich")
                        return decrypted_content
                    except Exception as e:
                        print(f"❌ Direkte Entschlüsselung fehlgeschlagen: {str(e)}")
                        raise ValueError(f"Entschlüsselung fehlgeschlagen: {str(e)}")
                raise ValueError("Keine IPFS-Referenz oder direkter Inhalt für dieses Modell gefunden")

            print(f"✅ IPFS CID gefunden: {ipfs_cid}")

            # Retrieve encrypted content from IPFS
            encrypted_content = self.ipfs.get(ipfs_cid)
            if not encrypted_content:
                print(f"❌ Inhalt konnte nicht aus IPFS abgerufen werden")
                raise ValueError("Inhalt konnte nicht aus IPFS abgerufen werden")

            print(f"✅ Inhalt aus IPFS abgerufen: {len(encrypted_content)} bytes")

            # Datei entschlüsseln
            try:
                key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                decrypted_content = decrypt_file(encrypted_content, key)
                print(f"✅ Entschlüsselung erfolgreich: {len(decrypted_content)} bytes")
                print(f"=== GET_MODEL_FILE DEBUG ENDE ===\n")
                return decrypted_content
            except Exception as e:
                print(f"❌ Entschlüsselung fehlgeschlagen: {str(e)}")
                raise ValueError(f"Entschlüsselung fehlgeschlagen: {str(e)}")

        except Exception as e:
            print(f"❌ Allgemeiner Fehler in get_model_file: {str(e)}")
            raise e
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

            # Verschlüsselte Datei finden
            encrypted_file = data_entry.encrypted_file
            if not encrypted_file:
                raise ValueError("Keine verschlüsselte Datei für diese Daten gefunden")

            # Verschlüsselungsschlüssel aus der Schlüssel-Datei laden
            encryption_key = self._load_encryption_key(data_id)
            if not encryption_key:
                raise ValueError(f"Verschlüsselungsschlüssel für {data_id} nicht gefunden")

            # Transaktion durchführen
            self.data_purchase_transaction(buyer_address, data_id, amount)

            # Beziehung aktualisieren
            if user not in data_entry.purchased_by:
                data_entry.purchased_by.append(user)

            session.commit()

            # Schlüssel für den Käufer speichern
            self._save_key_for_buyer(buyer_address, data_id, encryption_key, data_entry)

            return encryption_key
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

            # Verschlüsselte Datei finden
            encrypted_file = model_entry.encrypted_file
            if not encrypted_file:
                raise ValueError("Keine verschlüsselte Datei für dieses Modell gefunden")

            # Verschlüsselungsschlüssel aus der Schlüssel-Datei laden
            encryption_key = self._load_encryption_key(model_id)
            if not encryption_key:
                raise ValueError(f"Verschlüsselungsschlüssel für {model_id} nicht gefunden")

            # Transaktion durchführen
            self.model_purchase_transaction(buyer_address, model_id, amount)

            # Beziehung aktualisieren
            if user not in model_entry.purchased_by:
                model_entry.purchased_by.append(user)

            session.commit()

            # Schlüssel für den Käufer speichern
            self._save_key_for_buyer(buyer_address, model_id, encryption_key, model_entry)

            return encryption_key
        finally:
            session.close()

    def _load_encryption_key(self, item_id):
        """Lädt den Verschlüsselungsschlüssel für ein Item"""
        import os
        import json

        # Prüfe verschiedene Schlüssel-Dateien
        key_files = ['data_keys.json', 'EncryptionKeys.json']

        for key_file in key_files:
            if os.path.exists(key_file):
                try:
                    with open(key_file, 'r') as f:
                        keys_data = json.load(f)

                    datasets = keys_data.get('datasets', [])
                    for dataset in datasets:
                        if dataset.get('data_id') == item_id:
                            return dataset.get('encryption_key')
                except Exception as e:
                    print(f"Fehler beim Lesen von {key_file}: {e}")

        return None

    def _save_key_for_buyer(self, buyer_address, item_id, encryption_key, item_entry):
        """Speichert den Verschlüsselungsschlüssel für den Käufer"""
        import os
        import json
        from datetime import datetime

        # Lade oder erstelle data_keys.json
        keys_file = 'data_keys.json'
        if os.path.exists(keys_file):
            with open(keys_file, 'r') as f:
                keys_data = json.load(f)
        else:
            keys_data = {"datasets": []}

        # Bestimme den Namen je nach Item-Typ
        if hasattr(item_entry, 'data_metadata') and item_entry.data_metadata:
            try:
                metadata = json.loads(item_entry.data_metadata)
                item_name = metadata.get('name', 'Unknown Dataset')
            except:
                item_name = 'Unknown Dataset'
        elif hasattr(item_entry, 'model_metadata') and item_entry.model_metadata:
            try:
                metadata = json.loads(item_entry.model_metadata)
                item_name = metadata.get('name', 'Unknown Model')
            except:
                item_name = 'Unknown Model'
        else:
            item_name = 'Unknown Item'

        # Füge Eintrag für den Käufer hinzu (mit Käufer-Info)
        buyer_key_entry = {
            "name": item_name,
            "data_id": item_id,
            "encryption_key": encryption_key,
            "upload_date": datetime.now().strftime('%Y-%m-%d'),
            "purchased_by": buyer_address,  # Markiere als gekauft
            "purchase_date": datetime.now().strftime('%Y-%m-%d')
        }

        # Prüfe ob bereits vorhanden (vermeiden von Duplikaten)
        existing_entry = None
        for entry in keys_data["datasets"]:
            if (entry.get("data_id") == item_id and
                    entry.get("purchased_by") == buyer_address):
                existing_entry = entry
                break

        if not existing_entry:
            keys_data["datasets"].append(buyer_key_entry)

            # Speichere die aktualisierte Datei
            with open(keys_file, 'w') as f:
                json.dump(keys_data, f, indent=2)

            print(f"Verschlüsselungsschlüssel für Käufer {buyer_address} gespeichert")

    def get_data_file(self, user_address, data_id, encryption_key):
        """Gibt die entschlüsselte Datei zurück, wenn der Benutzer Zugriff hat.
        Holt den Inhalt aus IPFS statt direkt aus der Datenbank.
        KORRIGIERT: Prüft Blockchain direkt für Purchase-Berechtigung.

        Args:
            user_address: Adresse des Benutzers
            data_id: ID der Daten
            encryption_key: Entschlüsselungsschlüssel

        Returns:
            bytes: Entschlüsselte Datei
        """
        session = self.db_manager.get_session()
        try:
            print(f"\n=== GET_DATA_FILE DEBUG ===")
            print(f"User: {user_address}, Data ID: {data_id}")

            # Benutzer finden
            user = session.query(User).filter_by(address=user_address).first()
            if not user:
                print(f"❌ Benutzer mit Adresse {user_address} nicht in Datenbank gefunden")
                raise ValueError(f"Benutzer mit Adresse {user_address} nicht gefunden")

            print(f"✅ User gefunden: ID {user.id}")

            # Daten finden
            data_entry = session.query(DataEntry).filter_by(data_id=data_id).first()
            if not data_entry:
                print(f"❌ DataEntry mit ID {data_id} nicht gefunden")
                raise ValueError(f"Daten mit ID {data_id} nicht gefunden")

            print(f"✅ DataEntry gefunden: ID {data_entry.id}, Owner ID: {data_entry.owner_id}")

            # NEUE LOGIK: Überprüfen der Zugriffsberechtigung
            has_access = False
            access_reason = ""

            # 1. Prüfe ob User der Owner ist
            if data_entry.owner_id == user.id:
                has_access = True
                access_reason = "User ist Owner"
                print(f"✅ {access_reason}")
            else:
                print(f"⚠️ User ist nicht Owner (Owner ID: {data_entry.owner_id})")

                # 2. Prüfe Blockchain direkt nach Purchase-Transaktionen
                print(f"🔍 Suche in Blockchain nach Purchase-Transaktionen...")

                purchase_found = False
                for block_idx, block in enumerate(self.chain):
                    for tx_idx, tx in enumerate(block.transactions):
                        if (tx.get('type') in ['data_purchase', 'model_purchase']
                                and tx.get('buyer') == user_address):

                            purchased_item_id = tx.get('data_id') or tx.get('model_id')

                            if purchased_item_id == data_id:
                                purchase_found = True
                                access_reason = f"Purchase gefunden in Block {block_idx}, TX {tx_idx}"
                                print(f"✅ {access_reason}")
                                break

                    if purchase_found:
                        break

                if purchase_found:
                    has_access = True
                else:
                    print(f"❌ Keine Purchase-Transaktion gefunden")

                    # 3. Fallback: Prüfe auch ausstehende Transaktionen
                    print(f"🔍 Prüfe ausstehende Transaktionen...")
                    for tx in self.current_transactions:
                        if (tx.get('type') in ['data_purchase', 'model_purchase']
                                and tx.get('buyer') == user_address):

                            purchased_item_id = tx.get('data_id') or tx.get('model_id')

                            if purchased_item_id == data_id:
                                has_access = True
                                access_reason = "Purchase in ausstehenden Transaktionen gefunden"
                                print(f"✅ {access_reason}")
                                break

            # Finale Zugriffsprüfung
            if not has_access:
                print(f"❌ ZUGRIFF VERWEIGERT: Kein Zugriff auf Daten {data_id}")
                raise ValueError("Kein Zugriff auf diese Daten")

            print(f"✅ ZUGRIFF GEWÄHRT: {access_reason}")

            # Verschlüsselte Datei holen
            encrypted_file = data_entry.encrypted_file
            if not encrypted_file:
                print(f"❌ Keine verschlüsselte Datei gefunden")
                raise ValueError("Keine Datei für diese Daten gefunden")

            print(f"✅ Verschlüsselte Datei gefunden")

            # Get the IPFS CID from metadata or the encrypted_file record
            ipfs_cid = None
            metadata = json.loads(data_entry.data_metadata) if data_entry.data_metadata else {}
            ipfs_cid = metadata.get("ipfs_cid") or encrypted_file.ipfs_cid

            if not ipfs_cid:
                # Fallback zu direktem Inhalt falls kein IPFS CID (für Rückwärtskompatibilität)
                if encrypted_file.encrypted_content:
                    print(f"⚠️ Verwende direkten DB-Inhalt (kein IPFS)")
                    try:
                        key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                        decrypted_content = decrypt_file(encrypted_file.encrypted_content, key)
                        print(f"✅ Direkte Entschlüsselung erfolgreich")
                        return decrypted_content
                    except Exception as e:
                        print(f"❌ Direkte Entschlüsselung fehlgeschlagen: {str(e)}")
                        raise ValueError(f"Entschlüsselung fehlgeschlagen: {str(e)}")
                raise ValueError("Keine IPFS-Referenz oder direkter Inhalt für diese Daten gefunden")

            print(f"✅ IPFS CID gefunden: {ipfs_cid}")

            # Retrieve encrypted content from IPFS
            encrypted_content = self.ipfs.get(ipfs_cid)
            if not encrypted_content:
                print(f"❌ Inhalt konnte nicht aus IPFS abgerufen werden")
                raise ValueError("Inhalt konnte nicht aus IPFS abgerufen werden")

            print(f"✅ Inhalt aus IPFS abgerufen: {len(encrypted_content)} bytes")

            # Datei entschlüsseln
            try:
                key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                decrypted_content = decrypt_file(encrypted_content, key)
                print(f"✅ Entschlüsselung erfolgreich: {len(decrypted_content)} bytes")
                print(f"=== GET_DATA_FILE DEBUG ENDE ===\n")
                return decrypted_content
            except Exception as e:
                print(f"❌ Entschlüsselung fehlgeschlagen: {str(e)}")
                raise ValueError(f"Entschlüsselung fehlgeschlagen: {str(e)}")

        except Exception as e:
            print(f"❌ Allgemeiner Fehler in get_data_file: {str(e)}")
            raise e
        finally:
            session.close()

    def make_block(self, proof: int, difficulty: int = 4, mining_time: float = 0.0) -> Block:
        """
        Creates a new Block in the Blockchain
        :param proof: The proof of work
        :param difficulty: The difficulty used for mining
        :param mining_time: The actual time taken to mine this block in seconds
        :return: new Block
        """
        previous_block = self.last_block

        # Neuen Block erstellen mit Schwierigkeit und Mining-Zeit
        block = Block(
            index=len(self.chain),
            previous_hash=previous_block.hash,
            timestamp=time.time(),
            transactions=self.current_transactions,
            proof=proof,
            difficulty=difficulty,  # Store the difficulty used
            mining_time=mining_time,  # Store the actual mining time
        )

        # Reset current transactions
        self.current_transactions = []

        # Add Block to the chain
        self.chain.append(block)

        # Save block in db
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
                existing_block.difficulty = getattr(block, 'difficulty', 4)  # Update difficulty
                existing_block.mining_time = getattr(block, 'mining_time', 0.0)  # Update mining time
                existing_block.transactions_json = json.dumps(block.transactions)
            else:
                # Block neu anlegen
                block_entry = BlockEntry(
                    index=block.index,
                    previous_hash=block.previous_hash,
                    timestamp=block.timestamp,
                    proof=block.proof,
                    block_hash=block.hash,
                    difficulty=getattr(block, 'difficulty', 4),  # Store difficulty
                    mining_time=getattr(block, 'mining_time', 0.0),  # Store mining time
                    transactions_json=json.dumps(block.transactions)
                )
                session.add(block_entry)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

class IPFSMarketplaceIntegration:
    """
    Integrates the Marketplace blockchain with our simulated IPFS system
    for storing and retrieving ML data and models.
    """

    def __init__(self, blockchain, ipfs_storage_dir="ipfs_storage"):
        """
        Initialize the integration.

        Args:
            blockchain: The blockchain instance
            ipfs_storage_dir: Directory for IPFS storage
        """
        self.blockchain = blockchain
        self.ipfs = SimulatedIPFS(ipfs_storage_dir)

    def upload_data_to_ipfs(self, data_content, metadata=None):
        """
        Upload data to IPFS and return the CID.

        Args:
            data_content: Raw data content (bytes)
            metadata: Optional metadata about the data

        Returns:
            The CID of the stored data
        """
        if metadata is None:
            metadata = {}

        # Add data type to metadata
        metadata["type"] = "data"

        # Upload to IPFS
        cid = self.ipfs.add(data_content, metadata)

        # Pin for persistence
        self.ipfs.pin(cid)

        return cid

    def upload_model_to_ipfs(self, model_content, metadata=None):
        """
        Upload a model to IPFS and return the CID.

        Args:
            model_content: Raw model content (bytes)
            metadata: Optional metadata about the model

        Returns:
            The CID of the stored model
        """
        if metadata is None:
            metadata = {}

        # Add model type to metadata
        metadata["type"] = "model"

        # Upload to IPFS
        cid = self.ipfs.add(model_content, metadata)

        # Pin for persistence
        self.ipfs.pin(cid)

        return cid

    def get_content_from_ipfs(self, cid):
        """
        Retrieve content from IPFS by its CID.

        Args:
            cid: The content identifier

        Returns:
            The content or None if not found
        """
        return self.ipfs.get(cid)

    def create_data_transaction_with_ipfs(self, owner_address, file_content, metadata, price):
        """
        Create a data upload transaction using IPFS for storage.

        Args:
            owner_address: Address of data owner
            file_content: The data content (bytes)
            metadata: Metadata about the data
            price: Price for the data

        Returns:
            Tuple of (transaction_id, ipfs_cid)
        """
        # Upload to IPFS
        ipfs_cid = self.upload_data_to_ipfs(file_content, metadata)

        # Add IPFS reference to metadata
        ipfs_metadata = metadata.copy()
        ipfs_metadata["ipfs_cid"] = ipfs_cid

        # Create blockchain transaction
        transaction_id = self.blockchain.data_upload_transaction(
            owner=owner_address,
            metadata=ipfs_metadata,
            price=price
        )

        return transaction_id, ipfs_cid

    def create_model_transaction_with_ipfs(self, owner_address, model_content, metadata, price):
        """
        Create a model upload transaction using IPFS for storage.

        Args:
            owner_address: Address of model owner
            model_content: The model content (bytes)
            metadata: Metadata about the model
            price: Price for the model

        Returns:
            Tuple of (transaction_id, ipfs_cid)
        """
        # Upload to IPFS
        ipfs_cid = self.upload_model_to_ipfs(model_content, metadata)

        # Add IPFS reference to metadata
        ipfs_metadata = metadata.copy()
        ipfs_metadata["ipfs_cid"] = ipfs_cid

        # Create blockchain transaction
        transaction_id = self.blockchain.model_upload_transaction(
            owner=owner_address,
            metadata=ipfs_metadata,
            price=price
        )

        return transaction_id, ipfs_cid

    def retrieve_data_from_transaction(self, transaction_id):
        """
        Retrieve data content from a transaction's IPFS reference.

        Args:
            transaction_id: The blockchain transaction ID

        Returns:
            Tuple of (content, metadata) or (None, None) if not found
        """
        # Find transaction in blockchain
        transaction = None
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.get("transaction_id") == transaction_id:
                    transaction = tx
                    break
            if transaction:
                break

        if not transaction or transaction.get("type") != "data_upload":
            return None, None

        # Get IPFS CID from transaction
        ipfs_cid = transaction.get("metadata", {}).get("ipfs_cid")
        if not ipfs_cid:
            return None, None

        # Retrieve content from IPFS
        content = self.ipfs.get(ipfs_cid)
        metadata = self.ipfs.get_metadata(ipfs_cid)

        return content, metadata

    def model_training_transaction(self, trainer_address, dataset_id, model_metadata, model_cid):
        """
        Creates a transaction for model training

        Args:
            trainer_address: Address of the user training the model
            dataset_id: ID of the dataset used for training
            model_metadata: Model metadata including performance metrics
            model_cid: IPFS CID of the trained model

        Returns:
            str: Transaction ID of the training transaction
        """
        transaction_id = str(uuid.uuid4()).replace("-", "")

        transaction = {
            "type": "model_training",
            "trainer": trainer_address,
            "dataset_id": dataset_id,
            "model_cid": model_cid,
            "metadata": model_metadata,
            "timestamp": time.time(),
            "signature": "placeholder_signature",  # In a real implementation, this would be cryptographically signed
            "transaction_id": transaction_id
        }

        # Add transaction to current list
        self.current_transactions.append(transaction)

        return transaction_id

    def register_trained_model(self, owner_address, dataset_id, model_cid, model_metadata, price=0):
        """
        Registers a trained model in the system, combining training and upload transactions

        Args:
            owner_address: Address of the model owner/trainer
            dataset_id: ID of the dataset used for training
            model_cid: IPFS CID of the trained model
            model_metadata: Metadata about the model including performance metrics
            price: Price for the model (default: 0)

        Returns:
            tuple: (model_id, training_tx_id)
        """
        session = self.db_manager.get_session()
        try:
            # Create the training transaction
            training_tx_id = self.model_training_transaction(
                owner_address,
                dataset_id,
                model_metadata,
                model_cid
            )

            # Also create a model upload transaction
            upload_metadata = model_metadata.copy()
            upload_metadata["training_tx_id"] = training_tx_id
            upload_metadata["ipfs_cid"] = model_cid

            # Register the model in the marketplace
            model_id = self.model_upload_transaction(owner_address, upload_metadata, price)

            # Find the user
            user = self.register_user(owner_address)

            # Get the dataset entry to establish the link
            data_entry = session.query(DataEntry).filter_by(data_id=dataset_id).first()

            # Create the model entry
            model_entry = ModelEntry(
                model_id=model_id,
                owner_id=user.id,
                model_metadata=json.dumps(upload_metadata),
                price=price,
                timestamp=time.time()
            )
            session.add(model_entry)
            session.flush()  # ID generieren

            # Create a reference file in IPFS format
            encrypted_file = EncryptedFile(
                file_hash=hashlib.sha256(str(model_cid).encode()).hexdigest(),
                ipfs_cid=model_cid,
                encryption_key_hash="model_is_not_encrypted",  # Models don't need encryption for this demo
                model_entry_id=model_entry.id
            )
            session.add(encrypted_file)
            session.commit()

            return model_id, training_tx_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()