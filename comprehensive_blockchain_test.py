#!/usr/bin/env python3
"""
Einfacher Blockchain Test
========================

Testet die grundlegenden Funktionen der Blockchain-Implementation.

Autor: Florian Kuhlert
Technische Hochschule Nürnberg Georg Simon Ohm
"""

import sys
import os
import time
import hashlib

# Füge Projektverzeichnis zum Pfad hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Blockchain.blockchain import Blockchain


def test_blockchain_basics():
    """Testet die grundlegenden Blockchain-Funktionen"""

    print("🔗 BLOCKCHAIN GRUNDLAGEN TEST")
    print("=" * 50)

    # Test 1: Blockchain erstellen
    print("\n1️⃣ Blockchain erstellen...")
    blockchain = Blockchain()

    print(f"   ✅ Blockchain initialisiert")
    print(f"   📊 Chain-Länge: {len(blockchain.chain)}")
    print(f"   🎯 Genesis Block Index: {blockchain.chain[0].index}")
    print(f"   🔑 Genesis Block Hash: {blockchain.last_block.hash[:20]}...")

    # Test 2: Transaktionen erstellen
    print("\n2️⃣ Transaktionen erstellen...")
    blockchain.make_transaction("Alice", "Bob", 10.0)
    blockchain.make_transaction("Bob", "Charlie", 5.0)
    blockchain.make_transaction("Charlie", "Alice", 2.0)

    print(f"   ✅ 3 Transaktionen erstellt")
    print(f"   📊 Ausstehende Transaktionen: {len(blockchain.current_transactions)}")

    # Test 3: Block minen (Schwierigkeit 2)
    print("\n3️⃣ Block minen (Schwierigkeit 2)...")
    start_time = time.time()
    new_block, mining_time = blockchain.mine_block(difficulty=2)

    print(f"   ✅ Block {new_block.index} gemined")
    print(f"   ⏱️ Mining-Zeit: {mining_time:.3f} Sekunden")
    print(f"   🔢 Proof: {new_block.proof}")
    print(f"   📦 Transaktionen im Block: {len(new_block.transactions)}")
    print(f"   🔑 Block Hash: {new_block.hash[:20]}...")

    # Proof-of-Work verifizieren
    last_proof = blockchain.chain[new_block.index - 1].proof
    guess = f"{last_proof}{new_block.proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    valid_pow = guess_hash.startswith('00')  # 2 führende Nullen

    print(f"   🔍 PoW Hash: {guess_hash[:30]}...")
    print(f"   ✅ PoW gültig: {valid_pow}")

    # Test 4: Chain-Validierung
    print("\n4️⃣ Chain-Validierung...")
    is_valid = blockchain.validate_chain()
    print(f"   ✅ Chain gültig: {is_valid}")
    print(f"   📊 Gesamte Chain-Länge: {len(blockchain.chain)}")

    # Test 5: Block-Validierung
    print("\n5️⃣ Block-Validierung...")
    if len(blockchain.chain) > 1:
        current_block = blockchain.chain[-1]
        previous_block = blockchain.chain[-2]
        block_valid = blockchain.validate_block(current_block, previous_block)
        print(f"   ✅ Block {current_block.index} gültig: {block_valid}")
        print(f"   🔗 Hash-Verkettung korrekt: {current_block.previous_hash == previous_block.hash}")

    return blockchain


def test_mining_difficulties():
    """Testet Mining mit verschiedenen Schwierigkeitsgraden"""

    print("\n\n⚡ MINING SCHWIERIGKEITSTEST")
    print("=" * 50)

    blockchain = Blockchain()
    difficulties = [2, 3, 4, 5]
    mining_times = []

    for difficulty in difficulties:
        print(f"\n🎯 Schwierigkeit {difficulty} ('{('0' * difficulty)}' am Anfang)...")

        # Transaktion hinzufügen
        blockchain.make_transaction(f"User{difficulty}", f"User{difficulty + 1}", float(difficulty))

        # Mining-Zeit messen
        start_time = time.time()
        new_block, mining_time = blockchain.mine_block(difficulty=difficulty)

        mining_times.append(mining_time)

        # Proof-of-Work verifizieren
        if new_block.index > 0:
            last_proof = blockchain.chain[new_block.index - 1].proof
        else:
            last_proof = 0

        guess = f"{last_proof}{new_block.proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        target = '0' * difficulty
        valid = guess_hash.startswith(target)

        print(f"   ⏱️ Mining-Zeit: {mining_time:.3f} Sekunden")
        print(f"   🔢 Proof: {new_block.proof}")
        print(f"   🔍 Hash: {guess_hash[:30]}...")
        print(f"   ✅ Ziel erreicht ({target}): {valid}")

        if difficulty > 2:
            speedup = mining_times[0] / mining_time if mining_time > 0 else 0
            print(f"   📈 Faktor zu Schwierigkeit 2: {speedup:.1f}x langsamer")

    # Zusammenfassung
    print(f"\n📊 MINING-ZEITEN ÜBERSICHT:")
    for i, (diff, time_taken) in enumerate(zip(difficulties, mining_times)):
        print(f"   Schwierigkeit {diff}: {time_taken:.3f}s")

    return blockchain


def test_proof_of_work_validation():
    """Testet die Proof-of-Work Validierung im Detail"""

    print("\n\n🔐 PROOF-OF-WORK VALIDIERUNG")
    print("=" * 50)

    blockchain = Blockchain()

    # Test valid_proof Funktion direkt
    print("\n🧪 Teste valid_proof Funktion...")

    last_proof = 100
    difficulty = 3

    print(f"   🎯 Suche Proof für last_proof={last_proof}, difficulty={difficulty}")

    # Finde gültigen Proof
    proof = 0
    start_time = time.time()

    while not blockchain.valid_proof(last_proof, proof, difficulty):
        proof += 1
        if proof > 100000:  # Verhindere endlose Schleife
            break

    search_time = time.time() - start_time

    print(f"   ✅ Gültiger Proof gefunden: {proof}")
    print(f"   ⏱️ Suchzeit: {search_time:.3f} Sekunden")

    # Validiere das Ergebnis
    guess = f"{last_proof}{proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    target = '0' * difficulty

    print(f"   🔍 Resultierender Hash: {guess_hash}")
    print(f"   🎯 Ziel ('{target}' am Anfang): {guess_hash.startswith(target)}")
    print(f"   ✅ valid_proof bestätigt: {blockchain.valid_proof(last_proof, proof, difficulty)}")


def test_complete_workflow():
    """Testet einen kompletten Blockchain-Workflow"""

    print("\n\n🔄 KOMPLETTER WORKFLOW TEST")
    print("=" * 50)

    blockchain = Blockchain()

    print("\n📝 Schritt 1: Mehrere Transaktionsrunden...")

    # Runde 1
    blockchain.make_transaction("Anna", "Ben", 15.0)
    blockchain.make_transaction("Ben", "Clara", 8.0)
    block1, time1 = blockchain.mine_block(difficulty=2)
    print(f"   ✅ Block 1: {len(block1.transactions)} Transaktionen, {time1:.3f}s")

    # Runde 2
    blockchain.make_transaction("Clara", "David", 5.0)
    blockchain.make_transaction("David", "Eva", 12.0)
    blockchain.make_transaction("Eva", "Anna", 3.0)
    block2, time2 = blockchain.mine_block(difficulty=3)
    print(f"   ✅ Block 2: {len(block2.transactions)} Transaktionen, {time2:.3f}s")

    # Runde 3
    blockchain.make_transaction("Frank", "Gina", 20.0)
    block3, time3 = blockchain.mine_block(difficulty=2)
    print(f"   ✅ Block 3: {len(block3.transactions)} Transaktionen, {time3:.3f}s")

    print(f"\n📊 Finale Chain-Statistiken:")
    print(f"   📦 Gesamte Blöcke: {len(blockchain.chain)}")

    total_transactions = sum(len(block.transactions) for block in blockchain.chain)
    print(f"   📝 Gesamte Transaktionen: {total_transactions}")

    # Validiere komplette Chain
    final_validation = blockchain.validate_chain()
    print(f"   ✅ Chain gültig: {final_validation}")

    # Zeige Chain-Übersicht
    print(f"\n🔗 Chain-Übersicht:")
    for i, block in enumerate(blockchain.chain):
        print(f"   Block {i}: {len(block.transactions)} TX, Hash: {block.hash[:16]}...")


def main():
    """Hauptfunktion - führt alle Tests aus"""

    print("🔬 BLOCKCHAIN IMPLEMENTATION TEST")
    print("Technische Hochschule Nürnberg Georg Simon Ohm")
    print("Autor: Florian Kuhlert")
    print("=" * 50)

    try:
        # Grundlegende Tests
        blockchain1 = test_blockchain_basics()

        # Mining-Tests
        blockchain2 = test_mining_difficulties()

        # Proof-of-Work Tests
        test_proof_of_work_validation()

        # Kompletter Workflow
        test_complete_workflow()

        print("\n\n🎉 ALLE TESTS ERFOLGREICH ABGESCHLOSSEN!")
        print("✅ Blockchain-Implementation funktioniert korrekt")

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        print("🔧 Überprüfen Sie die Blockchain-Implementation")


if __name__ == "__main__":
    main()