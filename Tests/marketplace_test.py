# test_marketplace.py
from marketplace import MarketplaceBlockchain
import base64


def test_marketplace():
    # Blockchain-Marktplatz erstellen
    blockchain = MarketplaceBlockchain()

    print("Marktplatz initialisiert")

    # Einen Benutzer registrieren
    user_address = "test_user_123"
    user = blockchain.register_user(user_address)
    print(f"Benutzer registriert: {user_address}")

    # Testdaten erstellen
    test_data = b"Dies ist ein Test-Datensatz zum Testen des Blockchain-Marktplatzes."
    metadata = {
        "name": "Test-Datensatz",
        "description": "Ein einfacher Datensatz zum Testen",
        "format": "text/plain",
        "size": len(test_data)
    }
    price = 10

    # Daten hochladen
    print("\nDaten werden hochgeladen...")
    data_id, encryption_key = blockchain.upload_data_with_file(
        user_address, test_data, metadata, price
    )
    print(f"Daten hochgeladen mit ID: {data_id}")
    print(f"Verschlüsselungsschlüssel: {encryption_key}")

    # Daten abrufen und entschlüsseln
    print("\nDaten werden abgerufen...")
    decrypted_data = blockchain.get_data_file(
        user_address, data_id, encryption_key
    )
    print(f"Entschlüsselte Daten: {decrypted_data.decode()}")

    # Zweiten Benutzer zum Testen des Kaufs erstellen
    buyer_address = "test_buyer_456"
    buyer = blockchain.register_user(buyer_address)
    print(f"\nKäufer registriert: {buyer_address}")

    # Kauf simulieren
    print("\nKauf wird simuliert...")
    transaction_id = blockchain.data_purchase_transaction(buyer_address, data_id, price)
    print(f"Kauf-Transaktion erstellt: {transaction_id}")

    # Block minen, um die Transaktion zu verarbeiten
    print("\nBlock wird gemined...")
    new_block, mining_time = blockchain.mine_block(difficulty=2)  # Niedrige Schwierigkeit für Test
    print(f"Block gemined in {mining_time:.4f} Sekunden mit Index: {new_block.index}")

    print("\nTest abgeschlossen!")
    return blockchain


if __name__ == "__main__":
    test_marketplace()