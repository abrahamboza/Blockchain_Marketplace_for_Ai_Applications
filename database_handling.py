import os
import json
from Blockchain.blockchain import Block
import time
from marketplace import MarketplaceBlockchain
from database import User, DataEntry, ModelEntry, EncryptedFile


def reset_database():
    """
    Setzt die Datenbank zurück, um mit einer frischen Blockchain zu starten.
    Löscht die SQLite-Datenbankdatei und die data_keys.json.
    """
    try:
        # SQLite-Datenbankdatei löschen
        if os.path.exists('marketplace.db'):
            os.remove('marketplace.db')
            print("Datenbank zurückgesetzt.")

        # Auch die data_keys.json löschen, wenn vorhanden
        if os.path.exists('data_keys.json'):
            os.remove('data_keys.json')
            print("Schlüsseldatei zurückgesetzt.")

        # Neue leere data_keys.json erstellen
        with open('data_keys.json', 'w') as f:
            json.dump({"datasets": []}, f)
            print("Neue leere Schlüsseldatei erstellt.")

        return True
    except Exception as e:
        print(f"Fehler beim Zurücksetzen der Datenbank: {e}")
        return False


def initialize_blockchain_from_database(blockchain):
    """
    Initialisiert die Blockchain basierend auf den Einträgen in der Datenbank.

    Args:
        blockchain: Eine Instanz von MarketplaceBlockchain

    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        db_manager = blockchain.db_manager
        session_db = db_manager.get_session()

        try:
            # Prüfe, ob Blocks in der Datenbank existieren
            from database import BlockEntry

            # Blockchain-Instanz zurücksetzen
            blockchain.chain = []  # Bestehende Chain löschen
            blockchain.current_transactions = []  # Transaktionen zurücksetzen

            # Genesis-Block wurde bereits erstellt, entfernen
            if len(blockchain.chain) > 0:
                blockchain.chain = []

            # Blöcke aus der Datenbank laden
            blocks = session_db.query(BlockEntry).order_by(BlockEntry.index).all()

            if not blocks:
                print("Keine Blöcke in der Datenbank gefunden. Erstelle Genesis-Block.")
                blockchain.create_genesis_block()
                return True

            print(f"Gefundene Blöcke in der Datenbank: {len(blocks)}")

            # Blöcke wiederherstellen
            for block_entry in blocks:
                try:
                    # Transaktionen parsen
                    transactions = json.loads(block_entry.transactions_json)

                    # Block-Objekt erstellen
                    block = Block(
                        index=block_entry.index,
                        previous_hash=block_entry.previous_hash,
                        timestamp=block_entry.timestamp,
                        transactions=transactions,
                        proof=block_entry.proof,
                        hash=block_entry.block_hash
                    )

                    # Block zur Chain hinzufügen
                    blockchain.chain.append(block)
                    print(f"Block {block.index} wiederhergestellt")
                except Exception as block_error:
                    print(f"Fehler beim Wiederherstellen von Block {block_entry.index}: {block_error}")

            print("Blockchain aus Datenbank wiederhergestellt.")
            return True

        except Exception as inner_error:
            print(f"Innerer Fehler bei der Wiederherstellung der Blockchain: {inner_error}")
            return False
        finally:
            session_db.close()

    except Exception as e:
        print(f"Fehler bei der Wiederherstellung der Blockchain: {e}")
        return False


def handle_database_initialization(blockchain, reset_db=False):
    """
    Zentrale Funktion zur Initialisierung der Datenbank und Blockchain.
    Entweder wird die Datenbank zurückgesetzt oder die Blockchain
    aus der vorhandenen Datenbank wiederhergestellt.

    Args:
        blockchain: Eine Instanz von MarketplaceBlockchain
        reset_db: Bool, ob die Datenbank zurückgesetzt werden soll

    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    if reset_db:
        print("Datenbank wird zurückgesetzt...")
        if reset_database():
            print("Datenbank erfolgreich zurückgesetzt.")
            return True
        else:
            print("Fehler beim Zurücksetzen der Datenbank.")
            return False
    else:
        print("Versuche, Blockchain aus Datenbank wiederherzustellen...")
        if initialize_blockchain_from_database(blockchain):
            print("Blockchain erfolgreich initialisiert.")
            return True
        else:
            print("Fehler bei der Initialisierung der Blockchain.")
            return False