### Import Libraries ###
import hashlib
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import uuid


class Block:
    """
    One Block consists of:
    An Index (0,1,2,3,...)
    The Hash of the previous Block (except for the Genesis Block)
    A unix-timestamp
    A list of the transactions in this block
    A number for the PoW
    The difficulty used for mining this block
    The hashed block as a string
    """

    def __init__(self, index: int, previous_hash: str, timestamp: float,
                 transactions: List[Dict], proof: int = 0, difficulty: int = 4, hash: str = None) -> None:
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof = proof
        self.difficulty = difficulty  # NEW: Store the difficulty used for mining
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self) -> str:
        """"
        Calculates the SHA-256 hash of a Block
        :return: <str> SHA-256 hash of the Block
        """
        block_string = json.dumps(
            {
                "index": self.index,
                "previous_hash": self.previous_hash,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "proof": self.proof,
                "difficulty": self.difficulty,  # Include difficulty in hash calculation
            }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """"
        Convert block to dictionary for serialization
        """
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "proof": self.proof,
            "difficulty": self.difficulty,  # Include difficulty in serialization
            "hash": self.hash,
        }


class Blockchain:
    def __init__(self):
        self.chain = []  # List for saving the blocks in the chain
        self.current_transactions = []  # temporary memory for transactions to get mined into the next block
        self.nodes = set()  # Set for nodes in the Network

        # Listen für Daten und Modelle hinzufügen
        self.data_list = []  # Liste für alle Daten-Einträge
        self.model_list = []  # Liste für alle Modell-Einträge

        # Create Genesis Block
        self.create_genesis_block()

    def hash(self, block: Block) -> str:
        """"
        Creates a SHA-256 hash of a Block
        :param block: <Block> Block
        :return: <str> SHA-256 hash of the Block
        """
        # Make sure the dictionary is sorted to not get inconsistend Hashes
        block_string = json.dumps(block.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def create_genesis_block(self):
        """"
        Creates a genesis block
        """
        genesis_block = Block(
            index=0,
            previous_hash="0",
            timestamp=time.time(),
            transactions=[self.create_genesis_transaction()],
            # Random proof value set here
            proof=100
        )

        self.chain.append(genesis_block)
        return genesis_block

    def create_genesis_transaction(self) -> Dict:
        """
        Create the first transaction for the genesis block
        In real cryptocurrencys the token Distribution is done here
        """
        return {
            "sender": "0",
            "recipient": "genesis",
            "amount": 1,
            "timestamp": time.time(),
            # Signature is just a spaceholder here
            "signature": "0",
            "transaction_id": str(uuid.uuid4()).replace("-", "")
        }

    def make_transaction(self, sender: str, recipient: str, amount: float) -> str:
        """
        Creates a new transaction for the next Block to mine
        :param sender: address of the sender
        :param recipient: address of the recipient
        :param amount: amount to be transmitted
        :return: Index of the Block which the transaction will be hold
        """
        transaction = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "timestamp": time.time(),
            # Normally this would be created using kryptographic methods
            "signature": "placeholder_signature",
            "transaction_id": str(uuid.uuid4()).replace("-", "")
        }

        # Add transaction to the List
        self.current_transactions.append(transaction)

        # Return index of the block which will handle the transaction
        return self.last_block.index + 1

    def update_state(self) -> None:
        """
        updates the state of the blockchain using all transactions
        :return:
        """

        # Normally here we would synch all Account values and update them
        # >> maybe implement later

    def make_block(self, proof: int, difficulty: int = 4) -> Block:
        """
        Creates a new Block in the Blockchain
        :param proof: The proof of work
        :param difficulty: The difficulty used for mining
        :return: new Block
        """
        previous_block = self.last_block

        # Neuen Block erstellen mit Schwierigkeit
        block = Block(
            index=len(self.chain),
            previous_hash=previous_block.hash,
            timestamp=time.time(),
            transactions=self.current_transactions,
            proof=proof,
            difficulty=difficulty,  # Store the difficulty used
        )

        # Reset current transactions
        self.current_transactions = []

        # Add Block to the chain
        self.chain.append(block)
        return block

    def set_block_index(self, block: Block) -> None:
        """
        Sets the index of the Block in the Blockchain
        Mainly just there if blocks will be added from another source from the api
        Don't know if we are gonna use this tbh
        :param block:
        :return:
        """
        block.index = len(self.chain)

    @property
    def last_block(self) -> Block:
        """
        Returns the last Block in the Blockchain
        :return: last Block in the chain
        """
        return self.chain[-1]

    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """
        Validates a given Block by checking:
        previous block hash,
        index,
        PoW,
        validating all transactions in the Block
        :param block: Block to validate
        :param previous_block:
        :return: True if valid False otherwise
        """

        if block.previous_hash != previous_block.hash:
            return False

        if block.index != previous_block.index + 1:
            return False

        if not self.valid_proof(previous_block.proof, block.proof):
            return False

        for transaction in block.transactions:
            if not self.validate_transaction(transaction):
                return False

        return True

    def validate_chain(self, chain: List[Block] = None) -> bool:
        """
        Validates the chain
        :param chain: chain to validate
        :return: True if valid False otherwise
        """

        chain = chain or self.chain

        if len(chain) == 0:
            return False

        # Validate each block in the chain
        for i in range(1, len(chain)):
            if not self.validate_block(chain[i], chain[i - 1]):
                return False

        return True

    def consensus(self) -> bool:
        """
        Simple Consens algorithm >> find the longest chain
        :return: True if chain got replaced False if not
        """
        # Normally we would check the chains of other nodes here
        # and compare them but this will probably be implemented later or
        # not at all
        return False

    def proof_of_work(self, last_proof: int, difficulty: int = 4) -> tuple:
        """
        Simple proof (parallel to bitcoins PoW with adjustable difficulty)
        - find a number P' so that hash(P * P') has 'difficulty' leading zeros

        :param last_proof: <int> last proof
        :param difficulty: <int> number of leading zeros required (default: 4)
        :return: <tuple> New Proof and time taken in seconds
        """
        start_time = time.time()
        proof = 0
        while self.valid_proof(last_proof, proof, difficulty) is False:
            proof += 1

        end_time = time.time()
        time_taken = end_time - start_time
        return proof, time_taken

    def valid_proof(self, last_proof: int, proof: int, difficulty: int = 4) -> bool:
        """
        Validates a Proof: Has hash(last_proof, proof) 'difficulty' leading zeros
        :param last_proof: <int> last proof
        :param proof: <int> proof
        :param difficulty: <int> number of leading zeros required (default: 4)
        :return: True if correct False otherwise
        """

        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == "0" * difficulty

    def mine_block(self, difficulty=4) -> tuple:
        """
        Mines a new Block
        :param difficulty: <int> mining difficulty (number of leading zeros)
        :return: tuple of (new Block, time taken to mine)
        """

        # Do the PoW
        last_block = self.last_block
        last_proof = last_block.proof
        proof, mining_time = self.proof_of_work(last_proof, difficulty)

        # Create new Block with the used difficulty
        block = self.make_block(proof, difficulty)

        # Aktualisiere die purchased_by-Listen für Daten und Modelle basierend auf geminen Transaktionen
        for tx in block.transactions:
            if tx.get("type") == "data_purchase":
                buyer = tx.get("buyer")
                data_id = tx.get("data_id")
                # Finde den data_entry und füge den Käufer hinzu
                for data_entry in self.data_list:
                    if data_entry["data_id"] == data_id and buyer not in data_entry["purchased_by"]:
                        data_entry["purchased_by"].append(buyer)

            elif tx.get("type") == "model_purchase":
                buyer = tx.get("buyer")
                model_id = tx.get("model_id")
                # Finde den model_entry und füge den Käufer hinzu
                for model_entry in self.model_list:
                    if model_entry["model_id"] == model_id and buyer not in model_entry["purchased_by"]:
                        model_entry["purchased_by"].append(buyer)

        return block, mining_time

    # ---- Data-Marktplatz Funktionen ----

    def data_upload_transaction(self, owner: str, metadata: Dict, price: float) -> str:
        """
        Erstellt eine neue Transaktion für den Upload von Daten

        :param owner: Adresse des Datenbesitzers
        :param metadata: Metadaten der Daten (Format, Größe, Beschreibung, etc.)
        :param price: Preis der Daten
        :return: Transaktions-ID
        """
        transaction_id = str(uuid.uuid4()).replace("-", "")

        transaction = {
            "type": "data_upload",
            "owner": owner,
            "metadata": metadata,
            "price": price,
            "timestamp": time.time(),
            "signature": "placeholder_signature",  # In einer echten Implementierung wäre dies kryptografisch signiert
            "transaction_id": transaction_id
        }

        # Transaktion zur aktuellen Liste hinzufügen
        self.current_transactions.append(transaction)

        # Data-Entry in die data_list hinzufügen
        data_entry = {
            "data_id": transaction_id,
            "owner": owner,
            "metadata": metadata,
            "price": price,
            "timestamp": time.time(),
            "purchased_by": []
        }
        self.data_list.append(data_entry)

        return transaction_id

    def model_upload_transaction(self, owner: str, metadata: Dict, price: float) -> str:
        """
        Erstellt eine neue Transaktion für den Upload eines ML-Modells

        :param owner: Adresse des Modellbesitzers
        :param metadata: Metadaten des Modells (Typ, Hyperparameter, Performance, etc.)
        :param price: Preis des Modells
        :return: Transaktions-ID
        """
        transaction_id = str(uuid.uuid4()).replace("-", "")

        transaction = {
            "type": "model_upload",
            "owner": owner,
            "metadata": metadata,
            "price": price,
            "timestamp": time.time(),
            "signature": "placeholder_signature",
            "transaction_id": transaction_id
        }

        # Transaktion zur aktuellen Liste hinzufügen
        self.current_transactions.append(transaction)

        # Model-Entry in die model_list hinzufügen
        model_entry = {
            "model_id": transaction_id,
            "owner": owner,
            "metadata": metadata,
            "price": price,
            "timestamp": time.time(),
            "purchased_by": []
        }
        self.model_list.append(model_entry)

        return transaction_id

    def data_purchase_transaction(self, buyer: str, data_id: str, amount: float) -> str:
        """
        Erstellt eine neue Transaktion für den Kauf von Daten

        :param buyer: Adresse des Käufers
        :param data_id: ID der zu kaufenden Daten (Transaktions-ID der data_upload-Transaktion)
        :param amount: Betrag, der bezahlt wird
        :return: Transaktions-ID
        """
        transaction_id = str(uuid.uuid4()).replace("-", "")

        # Finde den Besitzer der Daten
        data_owner = None
        data_entry = None

        # Suche in der data_list
        for entry in self.data_list:
            if entry["data_id"] == data_id:
                data_owner = entry["owner"]
                data_entry = entry
                break

        if data_owner is None:
            # Suche in der Blockchain
            for block in self.chain:
                for tx in block.transactions:
                    if tx.get("type") == "data_upload" and tx.get("transaction_id") == data_id:
                        data_owner = tx.get("owner")
                        break

        if data_owner is None:
            # Suche auch in ausstehenden Transaktionen
            for tx in self.current_transactions:
                if tx.get("type") == "data_upload" and tx.get("transaction_id") == data_id:
                    data_owner = tx.get("owner")
                    break

        if data_owner is None:
            raise ValueError(f"Daten mit ID {data_id} nicht gefunden")

        transaction = {
            "type": "data_purchase",
            "buyer": buyer,
            "seller": data_owner,
            "data_id": data_id,
            "amount": amount,
            "timestamp": time.time(),
            "signature": "placeholder_signature",
            "transaction_id": transaction_id
        }

        # Transaktion zur aktuellen Liste hinzufügen
        self.current_transactions.append(transaction)

        # Aktualisiere die purchased_by Liste im data_entry, falls vorhanden
        if data_entry and buyer not in data_entry["purchased_by"]:
            data_entry["purchased_by"].append(buyer)

        return transaction_id

    def model_purchase_transaction(self, buyer: str, model_id: str, amount: float) -> str:
        """
        Erstellt eine neue Transaktion für den Kauf eines ML-Modells

        :param buyer: Adresse des Käufers
        :param model_id: ID des zu kaufenden Modells (Transaktions-ID der model_upload-Transaktion)
        :param amount: Betrag, der bezahlt wird
        :return: Transaktions-ID
        """
        transaction_id = str(uuid.uuid4()).replace("-", "")

        # Finde den Besitzer des Modells
        model_owner = None
        model_entry = None

        # Suche in der model_list
        for entry in self.model_list:
            if entry["model_id"] == model_id:
                model_owner = entry["owner"]
                model_entry = entry
                break

        if model_owner is None:
            # Suche in der Blockchain
            for block in self.chain:
                for tx in block.transactions:
                    if tx.get("type") == "model_upload" and tx.get("transaction_id") == model_id:
                        model_owner = tx.get("owner")
                        break

        if model_owner is None:
            # Suche auch in ausstehenden Transaktionen
            for tx in self.current_transactions:
                if tx.get("type") == "model_upload" and tx.get("transaction_id") == model_id:
                    model_owner = tx.get("owner")
                    break

        if model_owner is None:
            raise ValueError(f"Modell mit ID {model_id} nicht gefunden")

        transaction = {
            "type": "model_purchase",
            "buyer": buyer,
            "seller": model_owner,
            "model_id": model_id,
            "amount": amount,
            "timestamp": time.time(),
            "signature": "placeholder_signature",
            "transaction_id": transaction_id
        }

        # Transaktion zur aktuellen Liste hinzufügen
        self.current_transactions.append(transaction)

        # Aktualisiere die purchased_by Liste im model_entry, falls vorhanden
        if model_entry and buyer not in model_entry["purchased_by"]:
            model_entry["purchased_by"].append(buyer)

        return transaction_id

    def validate_transaction(self, transaction: Dict) -> bool:
        """
        Validiert eine gegebene Transaktion
        Erweitert um verschiedene Transaktionstypen

        :param transaction: Zu validierende Transaktion
        :return: True oder False
        """
        # Prüfe Transaktionstyp
        if "type" not in transaction:
            # Standard-Transaktion (Geldtransfer)
            if not all(k in transaction for k in ("sender", "recipient", "amount", "timestamp", "signature")):
                return False
        elif transaction["type"] == "data_upload":
            if not all(k in transaction for k in ("owner", "metadata", "price", "timestamp", "signature")):
                return False
        elif transaction["type"] == "model_upload":
            if not all(k in transaction for k in ("owner", "metadata", "price", "timestamp", "signature")):
                return False
        elif transaction["type"] == "data_purchase":
            if not all(k in transaction for k in ("buyer", "seller", "data_id", "amount", "timestamp", "signature")):
                return False
        elif transaction["type"] == "model_purchase":
            if not all(k in transaction for k in ("buyer", "seller", "model_id", "amount", "timestamp", "signature")):
                return False
        else:
            # Unbekannter Transaktionstyp
            return False

        # Hier könnten weitere Validierungen hinzugefügt werden, z.B.:
        # - Überprüfung der Signatur
        # - Überprüfung des Guthabens des Käufers
        # - Überprüfung, ob die Daten/Modelle existieren

        return True

    def get_data_listing(self) -> List[Dict]:
        """
        Gibt eine Liste aller verfügbaren Daten zurück

        :return: Liste von Daten-Metadaten
        """
        # Verwende die data_list direkt, da sie alle Daten enthält
        return self.data_list

    def get_model_listing(self) -> List[Dict]:
        """
        Gibt eine Liste aller verfügbaren ML-Modelle zurück

        :return: Liste von Modell-Metadaten
        """
        # Verwende die model_list direkt, da sie alle Modelle enthält
        return self.model_list