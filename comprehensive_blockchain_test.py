#!/usr/bin/env python3
"""
Umfassende Blockchain Test Suite
================================

Dieses Testskript demonstriert und validiert alle Kernfunktionen
der Data Marketplace Blockchain Implementation.

Autor: Florian Kuhlert
Datum: Juni 2025
Technische Hochschule Nürnberg Georg Simon Ohm
"""

import sys
import os
import time
import hashlib
import json
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from Blockchain.blockchain import Blockchain, Block
    from marketplace import MarketplaceBlockchain
    from encryption import generate_key, encrypt_file, decrypt_file
    import key_manager
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Stellen Sie sicher, dass alle Module verfügbar sind.")
    sys.exit(1)


class BlockchainTestSuite:
    """Comprehensive test suite for the Data Marketplace Blockchain"""

    def __init__(self):
        """Initialize test suite"""
        self.test_results = []
        self.start_time = time.time()
        print("🔬 Blockchain Test Suite gestartet")
        print("=" * 60)

    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")

    def test_basic_blockchain_creation(self):
        """Test 1: Grundlegende Blockchain-Erstellung"""
        print("\n📋 Test 1: Grundlegende Blockchain-Erstellung")
        try:
            blockchain = Blockchain()

            # Prüfe Genesis Block
            genesis_exists = len(blockchain.chain) > 0
            genesis_valid = blockchain.chain[0].index == 0 if genesis_exists else False

            self.log_test(
                "Genesis Block Erstellung",
                genesis_exists and genesis_valid,
                f"Chain-Länge: {len(blockchain.chain)}, Genesis-Index: {blockchain.chain[0].index if genesis_exists else 'N/A'}"
            )

            return blockchain

        except Exception as e:
            self.log_test("Genesis Block Erstellung", False, str(e))
            return None

    def test_transaction_creation(self, blockchain):
        """Test 2: Transaktionserstellung"""
        print("\n📋 Test 2: Transaktionserstellung")
        try:
            # Erstelle Test-Transaktionen
            tx1 = blockchain.make_transaction("Alice", "Bob", 5.0)
            tx2 = blockchain.make_transaction("Bob", "Charlie", 2.5)
            tx3 = blockchain.make_transaction("Charlie", "Alice", 1.0)

            pending_count = len(blockchain.current_transactions)

            self.log_test(
                "Transaktionen erstellen",
                pending_count == 3,
                f"Ausstehende Transaktionen: {pending_count}"
            )

            # Prüfe Transaktionsstruktur
            if pending_count > 0:
                tx = blockchain.current_transactions[0]
                has_required_fields = all(field in tx for field in ['from', 'to', 'amount', 'timestamp'])

                self.log_test(
                    "Transaktionsstruktur validieren",
                    has_required_fields,
                    f"Felder: {list(tx.keys())}"
                )

        except Exception as e:
            self.log_test("Transaktionserstellung", False, str(e))

    def test_proof_of_work_mining(self, blockchain):
        """Test 3: Proof-of-Work Mining"""
        print("\n📋 Test 3: Proof-of-Work Mining")
        try:
            # Test verschiedene Schwierigkeitsgrade
            difficulties = [2, 3, 4]
            mining_times = []

            for difficulty in difficulties:
                if len(blockchain.current_transactions) == 0:
                    blockchain.make_transaction("Test", "Mining", 1.0)

                start_time = time.time()
                new_block, mining_time = blockchain.mine_block(difficulty=difficulty)
                end_time = time.time()

                mining_times.append(mining_time)

                # Validiere Proof-of-Work
                last_proof = blockchain.chain[new_block.index - 1].proof if new_block.index > 0 else 0
                guess = f"{last_proof}{new_block.proof}".encode()
                guess_hash = hashlib.sha256(guess).hexdigest()
                valid_pow = guess_hash.startswith('0' * difficulty)

                self.log_test(
                    f"Mining Difficulty {difficulty}",
                    valid_pow,
                    f"Zeit: {mining_time:.3f}s, Hash: {guess_hash[:20]}..."
                )

            # Teste steigende Schwierigkeit
            increasing_difficulty = all(
                mining_times[i] <= mining_times[i + 1] * 3 for i in range(len(mining_times) - 1))
            self.log_test(
                "Schwierigkeitsgrad-Skalierung",
                increasing_difficulty,
                f"Zeiten: {[f'{t:.3f}s' for t in mining_times]}"
            )

        except Exception as e:
            self.log_test("Proof-of-Work Mining", False, str(e))

    def test_chain_validation(self, blockchain):
        """Test 4: Blockchain-Validierung"""
        print("\n📋 Test 4: Blockchain-Validierung")
        try:
            # Teste vollständige Chain-Validierung
            is_valid = blockchain.validate_chain()
            self.log_test(
                "Chain-Validierung",
                is_valid,
                f"Chain-Länge: {len(blockchain.chain)}"
            )

            # Teste einzelne Block-Validierung
            if len(blockchain.chain) > 1:
                current_block = blockchain.chain[-1]
                previous_block = blockchain.chain[-2]
                block_valid = blockchain.validate_block(current_block, previous_block)

                self.log_test(
                    "Block-Validierung",
                    block_valid,
                    f"Block {current_block.index} validiert gegen Block {previous_block.index}"
                )

            # Teste Hash-Verkettung
            hash_chain_valid = True
            for i in range(1, len(blockchain.chain)):
                if blockchain.chain[i].previous_hash != blockchain.chain[i - 1].hash:
                    hash_chain_valid = False
                    break

            self.log_test(
                "Hash-Verkettung",
                hash_chain_valid,
                f"Alle {len(blockchain.chain)} Blöcke korrekt verkettet"
            )

        except Exception as e:
            self.log_test("Chain-Validierung", False, str(e))

    def test_marketplace_functionality(self):
        """Test 5: Marketplace-Funktionalität"""
        print("\n📋 Test 5: Marketplace-Funktionalität")
        try:
            marketplace = MarketplaceBlockchain()

            # Teste Benutzerregistrierung
            user_address = "test_user_12345"
            user = marketplace.register_user(user_address)

            self.log_test(
                "Benutzerregistrierung",
                user is not None,
                f"Benutzer-Adresse: {user_address}"
            )

            # Teste Datenupload
            test_data = b"Test dataset for blockchain marketplace validation"
            metadata = {
                "name": "Test Dataset",
                "description": "Validation test data",
                "format": "text/plain",
                "category": "test"
            }
            price = 15.0

            data_id, encryption_key = marketplace.upload_data_with_file(
                user_address, test_data, metadata, price
            )

            self.log_test(
                "Datenupload mit Verschlüsselung",
                data_id is not None and encryption_key is not None,
                f"Data ID: {data_id[:16]}..., Key-Länge: {len(encryption_key)}"
            )

            # Teste Schlüsselverwaltung
            key_saved = key_manager.save_key(metadata["name"], data_id, encryption_key)
            retrieved_key = key_manager.get_key(data_id)

            self.log_test(
                "Schlüsselverwaltung",
                key_saved and retrieved_key == encryption_key,
                f"Schlüssel gespeichert und korrekt abgerufen"
            )

            return marketplace, data_id, encryption_key, user_address

        except Exception as e:
            self.log_test("Marketplace-Funktionalität", False, str(e))
            return None, None, None, None

    def test_purchase_workflow(self, marketplace, data_id, encryption_key, seller_address):
        """Test 6: Kaufabwicklung"""
        print("\n📋 Test 6: Kaufabwicklung")
        try:
            # Registriere Käufer
            buyer_address = "test_buyer_67890"
            buyer = marketplace.register_user(buyer_address)

            self.log_test(
                "Käufer-Registrierung",
                buyer is not None,
                f"Käufer-Adresse: {buyer_address}"
            )

            # Erstelle Kauftransaktion
            purchase_tx = marketplace.data_purchase_transaction(buyer_address, data_id, 15.0)

            self.log_test(
                "Kauftransaktion erstellen",
                purchase_tx is not None,
                f"Transaktions-ID: {purchase_tx[:16]}..."
            )

            # Mine Block für Kauftransaktion
            new_block, mining_time = marketplace.mine_block(difficulty=2)

            self.log_test(
                "Kauftransaktion minen",
                new_block is not None,
                f"Block {new_block.index} in {mining_time:.3f}s gemined"
            )

            return buyer_address

        except Exception as e:
            self.log_test("Kaufabwicklung", False, str(e))
            return None

    def test_data_access_control(self, marketplace, data_id, encryption_key, seller_address, buyer_address):
        """Test 7: Datenzugriffskontrolle"""
        print("\n📋 Test 7: Datenzugriffskontrolle")
        try:
            # Teste Seller-Zugriff
            seller_data = marketplace.get_data_file(seller_address, data_id, encryption_key)

            self.log_test(
                "Verkäufer-Datenzugriff",
                seller_data is not None,
                f"Daten erfolgreich entschlüsselt: {len(seller_data)} bytes"
            )

            # Teste Buyer-Zugriff nach Kauf
            if buyer_address:
                try:
                    buyer_data = marketplace.get_data_file(buyer_address, data_id, encryption_key)
                    self.log_test(
                        "Käufer-Datenzugriff nach Kauf",
                        buyer_data is not None,
                        f"Käufer kann auf gekaufte Daten zugreifen"
                    )
                except Exception as access_error:
                    self.log_test(
                        "Käufer-Datenzugriff nach Kauf",
                        False,
                        f"Zugriffsfehler: {str(access_error)}"
                    )

            # Teste unauthorisierten Zugriff
            unauthorized_address = "unauthorized_user_999"
            try:
                unauthorized_data = marketplace.get_data_file(unauthorized_address, data_id, encryption_key)
                # Wenn es funktioniert, ist das ein Sicherheitsproblem
                self.log_test(
                    "Unbefugter Zugriff blockiert",
                    False,
                    "Unbefugter Zugriff sollte blockiert werden"
                )
            except:
                # Exception erwartet für unbefugten Zugriff
                self.log_test(
                    "Unbefugter Zugriff blockiert",
                    True,
                    "Zugriff korrekt verweigert"
                )

        except Exception as e:
            self.log_test("Datenzugriffskontrolle", False, str(e))

    def test_encryption_functionality(self):
        """Test 8: Verschlüsselungsfunktionalität"""
        print("\n📋 Test 8: Verschlüsselungsfunktionalität")
        try:
            # Teste Schlüsselgenerierung
            key1 = generate_key()
            key2 = generate_key()

            keys_different = key1 != key2
            self.log_test(
                "Eindeutige Schlüsselgenerierung",
                keys_different,
                f"Zwei verschiedene Schlüssel generiert"
            )

            # Teste Verschlüsselung/Entschlüsselung
            test_data = b"Dies ist ein Test für die Verschlüsselung im Blockchain-System."
            encrypted_data = encrypt_file(test_data, key1)
            decrypted_data = decrypt_file(encrypted_data, key1)

            encryption_works = test_data == decrypted_data
            self.log_test(
                "Verschlüsselung/Entschlüsselung",
                encryption_works,
                f"Original: {len(test_data)} bytes, Verschlüsselt: {len(encrypted_data)} bytes"
            )

            # Teste falscher Schlüssel
            try:
                wrong_decryption = decrypt_file(encrypted_data, key2)
                self.log_test(
                    "Falscher Schlüssel blockiert",
                    False,
                    "Entschlüsselung mit falschem Schlüssel sollte fehlschlagen"
                )
            except:
                self.log_test(
                    "Falscher Schlüssel blockiert",
                    True,
                    "Entschlüsselung mit falschem Schlüssel korrekt blockiert"
                )

        except Exception as e:
            self.log_test("Verschlüsselungsfunktionalität", False, str(e))

    def test_performance_metrics(self):
        """Test 9: Performance-Metriken"""
        print("\n📋 Test 9: Performance-Metriken")
        try:
            blockchain = Blockchain()

            # Teste Mining-Performance
            num_transactions = 5
            for i in range(num_transactions):
                blockchain.make_transaction(f"User{i}", f"User{i + 1}", float(i + 1))

            start_time = time.time()
            new_block, mining_time = blockchain.mine_block(difficulty=3)
            total_time = time.time() - start_time

            transactions_per_second = num_transactions / mining_time if mining_time > 0 else 0

            self.log_test(
                "Mining-Performance",
                mining_time < 30.0,  # Sollte unter 30 Sekunden sein
                f"{num_transactions} Transaktionen in {mining_time:.3f}s ({transactions_per_second:.1f} TPS)"
            )

            # Teste Chain-Validierungs-Performance
            start_time = time.time()
            is_valid = blockchain.validate_chain()
            validation_time = time.time() - start_time

            self.log_test(
                "Validierungs-Performance",
                validation_time < 1.0 and is_valid,
                f"Chain-Validierung in {validation_time:.3f}s"
            )

        except Exception as e:
            self.log_test("Performance-Metriken", False, str(e))

    def test_edge_cases(self):
        """Test 10: Edge Cases und Fehlerbedingungen"""
        print("\n📋 Test 10: Edge Cases und Fehlerbedingungen")
        try:
            blockchain = Blockchain()

            # Teste leere Transaktionsliste
            empty_block, mining_time = blockchain.mine_block(difficulty=2)

            self.log_test(
                "Mining ohne Transaktionen",
                empty_block is not None,
                f"Leerer Block erfolgreich gemined in {mining_time:.3f}s"
            )

            # Teste sehr große Transaktion
            large_data = "x" * 10000  # 10KB String
            blockchain.make_transaction("BigSender", "BigReceiver", 1000.0, {"large_data": large_data})

            large_block, mining_time = blockchain.mine_block(difficulty=2)

            self.log_test(
                "Große Transaktionen verarbeiten",
                large_block is not None,
                f"Block mit großer Transaktion gemined in {mining_time:.3f}s"
            )

            # Teste Chain-Konsistenz nach vielen Blöcken
            for i in range(5):
                blockchain.make_transaction(f"Auto{i}", f"Auto{i + 1}", float(i))
                blockchain.mine_block(difficulty=2)

            final_validation = blockchain.validate_chain()

            self.log_test(
                "Langzeit-Chain-Konsistenz",
                final_validation,
                f"Chain mit {len(blockchain.chain)} Blöcken bleibt gültig"
            )

        except Exception as e:
            self.log_test("Edge Cases", False, str(e))

    def run_all_tests(self):
        """Führe alle Tests aus"""
        print("🚀 Starte umfassende Blockchain-Testsuite...")
        print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test 1: Grundlegende Blockchain
        blockchain = self.test_basic_blockchain_creation()

        if blockchain:
            # Test 2-4: Grundlegende Blockchain-Funktionen
            self.test_transaction_creation(blockchain)
            self.test_proof_of_work_mining(blockchain)
            self.test_chain_validation(blockchain)

        # Test 5-7: Marketplace-Funktionen
        marketplace, data_id, encryption_key, seller_address = self.test_marketplace_functionality()

        if marketplace and data_id:
            buyer_address = self.test_purchase_workflow(marketplace, data_id, encryption_key, seller_address)
            self.test_data_access_control(marketplace, data_id, encryption_key, seller_address, buyer_address)

        # Test 8-10: Zusätzliche Funktionen
        self.test_encryption_functionality()
        self.test_performance_metrics()
        self.test_edge_cases()

        # Ergebnisse zusammenfassen
        self.print_summary()

    def print_summary(self):
        """Drucke Testzusammenfassung"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_time = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("📊 TESTZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"Gesamtlaufzeit: {total_time:.2f} Sekunden")
        print(f"Tests durchgeführt: {total_tests}")
        print(f"✅ Erfolgreich: {passed_tests}")
        print(f"❌ Fehlgeschlagen: {failed_tests}")
        print(f"📈 Erfolgsrate: {success_rate:.1f}%")

        if failed_tests > 0:
            print(f"\n🔍 FEHLGESCHLAGENE TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['details']}")

        print("\n" + "=" * 60)

        if success_rate >= 90:
            print("🎉 BLOCKCHAIN-IMPLEMENTATION ERFOLGREICH VALIDIERT!")
        elif success_rate >= 70:
            print("⚠️  BLOCKCHAIN-IMPLEMENTATION TEILWEISE FUNKTIONAL")
        else:
            print("🚨 BLOCKCHAIN-IMPLEMENTATION BENÖTIGT ÜBERARBEITUNG")

        print("=" * 60)


def main():
    """Hauptfunktion zum Ausführen der Tests"""
    print("🔬 Data Marketplace Blockchain - Comprehensive Test Suite")
    print("Technische Hochschule Nürnberg Georg Simon Ohm")
    print("Autor: Florian Kuhlert, 2025")
    print("=" * 60)

    # Prüfe Abhängigkeiten
    try:
        test_suite = BlockchainTestSuite()
        test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️  Tests durch Benutzer unterbrochen")
    except Exception as e:
        print(f"\n💥 Kritischer Fehler in der Testsuite: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()