# test_blockchain.py
from Blockchain.blockchain import Blockchain, Block
import hashlib


def test_blockchain():
    # Blockchain erstellen
    blockchain = Blockchain()

    # Initialen Zustand überprüfen
    print("Blockchain initialisiert")
    print(f"Länge der Blockchain: {len(blockchain.chain)}")
    print(f"Genesis-Block-Hash: {blockchain.last_block.hash}")

    # Schwierigkeitsgrad festlegen
    difficulty = 4
    print(f"\nMining mit Schwierigkeitsgrad: {difficulty} (Anzahl führender Nullen)")

    # Einige Transaktionen erstellen
    print("\nTransaktionen erstellen...")
    blockchain.make_transaction("Alice", "Bob", 5)
    blockchain.make_transaction("Bob", "Charlie", 2)
    blockchain.make_transaction("Charlie", "Alice", 1)

    print(f"Ausstehende Transaktionen: {len(blockchain.current_transactions)}")

    # Block minen
    print("\nMining eines neuen Blocks...")
    last_proof = blockchain.last_block.proof
    new_block, mining_time = blockchain.mine_block(difficulty)

    print(f"Neuer Block erstellt mit Index: {new_block.index}")
    print(f"Proof: {new_block.proof}")
    print(f"Mining-Zeit: {mining_time:.4f} Sekunden")

    # Hash des Proofs überprüfen und anzeigen
    guess = f"{last_proof}{new_block.proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    print(f"Hash von {last_proof} + {new_block.proof}: {guess_hash}")
    print(f"Hat der Hash {difficulty} führende Nullen? {guess_hash[:difficulty] == '0' * difficulty}")

    print(f"Anzahl der Transaktionen im Block: {len(new_block.transactions)}")
    print(f"Ausstehende Transaktionen nach Mining: {len(blockchain.current_transactions)}")

    # Weitere Transaktionen und Mining mit erhöhter Schwierigkeit
    print("\nWeitere Transaktionen und Mining mit erhöhter Schwierigkeit...")
    blockchain.make_transaction("David", "Emma", 10)
    blockchain.make_transaction("Emma", "Frank", 3)

    # Schwierigkeit erhöhen
    higher_difficulty = 5
    print(f"Mining mit Schwierigkeitsgrad: {higher_difficulty}")

    last_proof = blockchain.last_block.proof
    another_block, mining_time_higher = blockchain.mine_block(higher_difficulty)
    print(f"Weiterer Block erstellt mit Index: {another_block.index}")
    print(f"Mining-Zeit: {mining_time_higher:.4f} Sekunden")

    # Auch für den zweiten Block den Hash überprüfen
    guess = f"{last_proof}{another_block.proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    print(f"Hash von {last_proof} + {another_block.proof}: {guess_hash}")
    print(
        f"Hat der Hash {higher_difficulty} führende Nullen? {guess_hash[:higher_difficulty] == '0' * higher_difficulty}")

    # Zeige den Unterschied in der Mining-Zeit
    print(f"\nVergleich der Mining-Zeiten:")
    print(f"Difficulty {difficulty}: {mining_time:.4f} Sekunden")
    print(f"Difficulty {higher_difficulty}: {mining_time_higher:.4f} Sekunden")
    print(f"Faktor: {mining_time_higher / mining_time:.2f}x länger")

    # Gesamte Kette anzeigen
    print("\nGesamte Blockchain:")
    for block in blockchain.chain:
        print(f"Block {block.index}: {len(block.transactions)} Transaktionen, Hash: {block.hash[:10]}...")

    return blockchain


if __name__ == "__main__":
    test_blockchain()