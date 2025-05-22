from flask import Flask, render_template, request, redirect, url_for, flash, session , jsonify
from Blockchain.blockchain import Blockchain
import os
import json
import hashlib
import uuid
from functools import wraps
from datetime import datetime
import time
import json


# Flask App Initialisierung
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'entwicklungsschluessel')

# Blockchain Instanz erstellen
blockchain = Blockchain()

# Benutzerdaten-Datei
USERS_FILE = 'users.json'


# Benutzerverwaltungsfunktionen
def load_users():
    """Lädt Benutzer aus der JSON-Datei."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_users(users):
    """Speichert Benutzer in der JSON-Datei."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def hash_password(password):
    """Einfache Passwort-Hash-Funktion."""
    return hashlib.sha256(password.encode()).hexdigest()


# Erstelle Demo-Benutzer beim Start
def initialize():
    users = load_users()
    if "demo" not in users:
        users["demo"] = {
            "username": "demo",
            "password_hash": hash_password("password"),
            "blockchain_address": str(uuid.uuid4()).replace('-', '')
        }
        save_users(users)
        print("Demo-Benutzer erstellt.")


initialize()


# Login-Check Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Bitte melde dich an, um auf diese Seite zuzugreifen.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Template-Hilfsfunktionen
@app.context_processor
def utility_processor():
    def is_logged_in():
        return 'username' in session

    def current_user():
        if 'username' in session:
            username = session['username']
            users = load_users()
            if username in users:
                user_data = users[username].copy()
                user_data.pop('password_hash', None)
                return user_data
        return None

    def format_timestamp(timestamp):
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%d.%m.%Y, %H:%M:%S")

    def format_address(address, start_chars=6, end_chars=4):
        if not address or len(address) <= start_chars + end_chars:
            return address
        return f"{address[:start_chars]}...{address[-end_chars:]}"

    return dict(
        is_logged_in=is_logged_in,
        current_user=current_user,
        format_timestamp=format_timestamp,
        format_address=format_address
    )


# Routen
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'

        users = load_users()

        if username in users and users[username]['password_hash'] == hash_password(password):
            # Benutzer in der Session speichern
            session['username'] = username
            session['blockchain_address'] = users[username]['blockchain_address']

            # Wenn "Angemeldet bleiben" aktiviert ist
            if remember_me:
                session.permanent = True

            flash(f'Willkommen zurück, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password:
            flash('Bitte fülle alle Pflichtfelder aus.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Die Passwörter stimmen nicht überein.', 'danger')
            return render_template('register.html')

        users = load_users()

        if username in users:
            flash('Dieser Benutzername ist bereits vergeben.', 'danger')
            return render_template('register.html')

        # Neuen Benutzer erstellen
        users[username] = {
            "username": username,
            "password_hash": hash_password(password),
            "blockchain_address": str(uuid.uuid4()).replace('-', '')
        }

        save_users(users)

        # Automatisch einloggen
        session['username'] = username
        session['blockchain_address'] = users[username]['blockchain_address']

        flash('Dein Konto wurde erfolgreich erstellt!', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('blockchain_address', None)
    flash('Du wurdest erfolgreich abgemeldet.', 'success')
    return redirect(url_for('index'))


# Placeholder-Routen für andere Seiten

@app.route('/upload-dataset')
def upload_dataset():
    flash('Die Upload-Funktion ist in Entwicklung.', 'info')
    return redirect(url_for('index'))


@app.route('/training/dashboard')
@login_required
def training_dashboard():
    flash('Das ML-Training Dashboard ist in Entwicklung.', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin():
    flash('Der Admin-Bereich ist in Entwicklung.', 'info')
    return redirect(url_for('index'))


# Einfacher Geschützer Bereich als Test
@app.route('/secured')
@login_required
def secured_page():
    return f'Geschützter Bereich - Hallo {session["username"]}!'


# Fehlerbehandlung
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# Blockchain Explorer Route - Füge dies zu deiner app.py hinzu

from datetime import datetime
import time


# Blockchain Explorer Route
@app.route('/blockchain')
def blockchain_explorer():
    """Hauptseite des Blockchain Explorers mit Live-Übersicht"""

    try:
        # Level 1: Live Blockchain-Übersicht
        blockchain_stats = {
            'total_blocks': len(blockchain.chain),
            'latest_block_index': blockchain.last_block.index,
            'latest_block_hash': blockchain.last_block.hash,
            'pending_transactions': len(blockchain.current_transactions),
            'total_transactions': sum(len(block.transactions) for block in blockchain.chain),
            'network_difficulty': 4,  # Standard-Schwierigkeit
            'average_block_time': '~30 seconds',  # Simuliert
            'last_mined': blockchain.last_block.timestamp if blockchain.chain else time.time()
        }

        # Letzte 5 Blöcke für Übersicht
        recent_blocks = []
        for block in reversed(blockchain.chain[-5:]):  # Letzte 5 Blöcke
            block_info = {
                'index': block.index,
                'hash': block.hash,
                'previous_hash': block.previous_hash,
                'timestamp': block.timestamp,
                'transaction_count': len(block.transactions),
                'proof': block.proof,
                'size_kb': len(str(block.transactions)) / 1024  # Approximierte Größe
            }
            recent_blocks.append(block_info)

        # Letzte 10 Transaktionen aus allen Blöcken
        recent_transactions = []
        transaction_count = 0

        # Durchsuche Blöcke rückwärts für die neuesten Transaktionen
        for block in reversed(blockchain.chain):
            for transaction in reversed(block.transactions):
                if transaction_count >= 10:
                    break

                # Bestimme Transaktions-Typ für bessere Anzeige
                tx_type = transaction.get('type', 'transfer')
                if tx_type == 'data_upload':
                    tx_display = {
                        'id': transaction.get('transaction_id', 'N/A')[:16] + '...',
                        'type': 'Data Upload',
                        'from_to': f"Upload by {transaction.get('owner', 'Unknown')[:20]}...",
                        'amount': f"${transaction.get('price', 0)}",
                        'timestamp': block.timestamp,
                        'status': 'Confirmed',
                        'block_index': block.index
                    }
                elif tx_type == 'model_upload':
                    tx_display = {
                        'id': transaction.get('transaction_id', 'N/A')[:16] + '...',
                        'type': 'Model Upload',
                        'from_to': f"Upload by {transaction.get('owner', 'Unknown')[:20]}...",
                        'amount': f"${transaction.get('price', 0)}",
                        'timestamp': block.timestamp,
                        'status': 'Confirmed',
                        'block_index': block.index
                    }
                elif tx_type == 'data_purchase':
                    tx_display = {
                        'id': transaction.get('transaction_id', 'N/A')[:16] + '...',
                        'type': 'Data Purchase',
                        'from_to': f"{transaction.get('buyer', 'Unknown')[:15]}... → {transaction.get('seller', 'Unknown')[:15]}...",
                        'amount': f"${transaction.get('amount', 0)}",
                        'timestamp': block.timestamp,
                        'status': 'Confirmed',
                        'block_index': block.index
                    }
                elif tx_type == 'model_purchase':
                    tx_display = {
                        'id': transaction.get('transaction_id', 'N/A')[:16] + '...',
                        'type': 'Model Purchase',
                        'from_to': f"{transaction.get('buyer', 'Unknown')[:15]}... → {transaction.get('seller', 'Unknown')[:15]}...",
                        'amount': f"${transaction.get('amount', 0)}",
                        'timestamp': block.timestamp,
                        'status': 'Confirmed',
                        'block_index': block.index
                    }
                else:
                    # Standard Transfer
                    tx_display = {
                        'id': transaction.get('transaction_id', 'N/A')[:16] + '...',
                        'type': 'Transfer',
                        'from_to': f"{transaction.get('sender', 'Unknown')[:15]}... → {transaction.get('recipient', 'Unknown')[:15]}...",
                        'amount': f"${transaction.get('amount', 0)}",
                        'timestamp': block.timestamp,
                        'status': 'Confirmed',
                        'block_index': block.index
                    }

                recent_transactions.append(tx_display)
                transaction_count += 1

            if transaction_count >= 10:
                break

        # Ausstehende Transaktionen hinzufügen
        for transaction in blockchain.current_transactions[:5]:  # Max 5 pending
            tx_type = transaction.get('type', 'transfer')

            if tx_type == 'data_upload':
                pending_tx = {
                    'id': transaction.get('transaction_id', 'N/A')[:16] + '...',
                    'type': 'Data Upload',
                    'from_to': f"Upload by {transaction.get('owner', 'Unknown')[:20]}...",
                    'amount': f"${transaction.get('price', 0)}",
                    'timestamp': time.time(),
                    'status': 'Pending',
                    'block_index': 'Pending'
                }
            else:
                pending_tx = {
                    'id': transaction.get('transaction_id', 'N/A')[:16] + '...',
                    'type': 'Transfer',
                    'from_to': f"{transaction.get('sender', 'Unknown')[:15]}... → {transaction.get('recipient', 'Unknown')[:15]}...",
                    'amount': f"${transaction.get('amount', 0)}",
                    'timestamp': time.time(),
                    'status': 'Pending',
                    'block_index': 'Pending'
                }

            recent_transactions.insert(0, pending_tx)  # Pending oben anzeigen

        return render_template('blockchain.html',
                               stats=blockchain_stats,
                               recent_blocks=recent_blocks,
                               recent_transactions=recent_transactions)

    except Exception as e:
        flash(f'Fehler beim Laden des Blockchain Explorers: {str(e)}', 'danger')
        return redirect(url_for('index'))


# API-Endpunkt für Block-Details (Level 2)
@app.route('/blockchain/block/<int:block_index>')
def block_details(block_index):
    """Detailansicht eines spezifischen Blocks"""

    try:
        # Prüfe ob Block-Index existiert
        if block_index < 0 or block_index >= len(blockchain.chain):
            flash(f'Block {block_index} nicht gefunden.', 'warning')
            return redirect(url_for('blockchain_explorer'))

        # Hole den Block
        block = blockchain.chain[block_index]

        # Level 2: Block-Details
        block_details = {
            'index': block.index,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'timestamp': block.timestamp,
            'proof': block.proof,
            'transaction_count': len(block.transactions),
            'block_size': len(str(block.transactions)),  # Größe in Bytes
            'formatted_timestamp': datetime.fromtimestamp(block.timestamp).strftime("%d.%m.%Y, %H:%M:%S"),
        }

        # Mining-Details berechnen
        if block_index > 0:
            previous_block = blockchain.chain[block_index - 1]
            mining_time = block.timestamp - previous_block.timestamp
            block_details['mining_time'] = f"{mining_time:.2f} seconds"
        else:
            block_details['mining_time'] = "Genesis Block"

        # Proof-of-Work Verification
        if block_index > 0:
            last_proof = blockchain.chain[block_index - 1].proof
            current_proof = block.proof
            guess = f"{last_proof}{current_proof}".encode()
            guess_hash = hashlib.sha256(guess).hexdigest()

            block_details['pow_verification'] = {
                'last_proof': last_proof,
                'current_proof': current_proof,
                'combined_hash': guess_hash,
                'leading_zeros': len(guess_hash) - len(guess_hash.lstrip('0')),
                'is_valid': guess_hash.startswith('0000')  # Standard difficulty 4
            }
        else:
            block_details['pow_verification'] = None

        # Detaillierte Transaktions-Liste
        detailed_transactions = []
        for idx, transaction in enumerate(block.transactions):
            tx_detail = {
                'index_in_block': idx,
                'transaction_id': transaction.get('transaction_id', 'N/A'),
                'type': transaction.get('type', 'transfer'),
                'timestamp': transaction.get('timestamp', block.timestamp),
                'signature': transaction.get('signature', 'N/A'),
                'raw_data': transaction  # Vollständige Transaktion für Details
            }

            # Typ-spezifische Details
            if transaction.get('type') == 'data_upload':
                tx_detail.update({
                    'owner': transaction.get('owner', 'Unknown'),
                    'price': transaction.get('price', 0),
                    'metadata': transaction.get('metadata', {}),
                })
            elif transaction.get('type') == 'model_upload':
                tx_detail.update({
                    'owner': transaction.get('owner', 'Unknown'),
                    'price': transaction.get('price', 0),
                    'metadata': transaction.get('metadata', {}),
                })
            elif transaction.get('type') in ['data_purchase', 'model_purchase']:
                tx_detail.update({
                    'buyer': transaction.get('buyer', 'Unknown'),
                    'seller': transaction.get('seller', 'Unknown'),
                    'amount': transaction.get('amount', 0),
                    'item_id': transaction.get('data_id') or transaction.get('model_id', 'Unknown'),
                })
            else:
                # Standard Transfer
                tx_detail.update({
                    'sender': transaction.get('sender', 'Unknown'),
                    'recipient': transaction.get('recipient', 'Unknown'),
                    'amount': transaction.get('amount', 0),
                })

            detailed_transactions.append(tx_detail)

        # Navigation zu vorherigen/nächsten Blöcken
        navigation = {
            'has_previous': block_index > 0,
            'previous_index': block_index - 1 if block_index > 0 else None,
            'has_next': block_index < len(blockchain.chain) - 1,
            'next_index': block_index + 1 if block_index < len(blockchain.chain) - 1 else None
        }

        return render_template('block_details.html',
                               block=block_details,
                               transactions=detailed_transactions,
                               navigation=navigation)

    except Exception as e:
        flash(f'Fehler beim Laden von Block {block_index}: {str(e)}', 'danger')
        return redirect(url_for('blockchain_explorer'))


# API-Endpunkt für Live-Updates (AJAX)
@app.route('/api/blockchain/stats')
def blockchain_stats_api():
    """JSON-API für Live-Updates des Blockchain Explorers"""

    try:
        stats = {
            'total_blocks': len(blockchain.chain),
            'latest_block_index': blockchain.last_block.index,
            'latest_block_hash': blockchain.last_block.hash[:16] + '...',
            'pending_transactions': len(blockchain.current_transactions),
            'total_transactions': sum(len(block.transactions) for block in blockchain.chain),
            'last_update': time.time()
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


#######################
# MARKETPLACE
#######################
# Mock-Daten für Demo-Zwecke (erweitert die Blockchain-Daten)
def initialize_demo_marketplace_data():
    """Fügt Demo-Daten zur Blockchain hinzu, falls sie leer ist"""

    # Prüfe ob bereits Marketplace-Daten existieren
    marketplace_transactions = []
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.get('type') in ['data_upload', 'model_upload']:
                marketplace_transactions.append(tx)

    # Wenn keine Marketplace-Daten vorhanden, füge Demo-Daten hinzu
    if len(marketplace_transactions) < 3:
        print("Füge Demo-Marketplace-Daten hinzu...")

        # Demo-Datensätze
        demo_datasets = [
            {
                'owner': 'alice_researcher',
                'metadata': {
                    'name': 'Customer Behavior Dataset',
                    'description': 'Comprehensive analysis of customer purchasing patterns with demographics',
                    'category': 'Business Analytics',
                    'format': 'CSV',
                    'size': '2.5MB',
                    'samples': 50000,
                    'features': 15,
                    'tags': ['customer', 'behavior', 'sales', 'demographics'],
                    'quality_score': 9.2,
                    'last_updated': '2025-05-20'
                },
                'price': 25.99
            },
            {
                'owner': 'data_science_lab',
                'metadata': {
                    'name': 'Medical Imaging Dataset',
                    'description': 'Annotated X-ray images for pneumonia detection research',
                    'category': 'Healthcare',
                    'format': 'Images + JSON',
                    'size': '12.8GB',
                    'samples': 5863,
                    'features': 'Image + Labels',
                    'tags': ['medical', 'xray', 'pneumonia', 'healthcare', 'imaging'],
                    'quality_score': 9.8,
                    'last_updated': '2025-05-18'
                },
                'price': 199.99
            },
            {
                'owner': 'finance_corp',
                'metadata': {
                    'name': 'Stock Market Prediction Data',
                    'description': 'Historical stock prices with technical indicators and news sentiment',
                    'category': 'Finance',
                    'format': 'CSV + Text',
                    'size': '890MB',
                    'samples': 1200000,
                    'features': 28,
                    'tags': ['stocks', 'finance', 'prediction', 'sentiment', 'trading'],
                    'quality_score': 8.7,
                    'last_updated': '2025-05-22'
                },
                'price': 89.50
            },
            {
                'owner': 'iot_solutions',
                'metadata': {
                    'name': 'Smart Home Sensor Data',
                    'description': 'IoT sensor readings from smart homes for energy optimization',
                    'category': 'IoT',
                    'format': 'Time Series JSON',
                    'size': '1.2GB',
                    'samples': 2800000,
                    'features': 12,
                    'tags': ['iot', 'smart-home', 'energy', 'sensors', 'time-series'],
                    'quality_score': 8.9,
                    'last_updated': '2025-05-21'
                },
                'price': 45.00
            }
        ]

        # Demo-Modelle
        demo_models = [
            {
                'owner': 'ml_expert',
                'metadata': {
                    'name': 'Advanced Image Classifier',
                    'description': 'Pre-trained CNN for general image classification with 95% accuracy',
                    'category': 'Computer Vision',
                    'framework': 'TensorFlow',
                    'model_type': 'Convolutional Neural Network',
                    'accuracy': '95.2%',
                    'parameters': '23.5M',
                    'input_size': '224x224x3',
                    'tags': ['cnn', 'image-classification', 'tensorflow', 'computer-vision'],
                    'training_dataset': 'ImageNet + Custom',
                    'last_updated': '2025-05-19'
                },
                'price': 299.99
            },
            {
                'owner': 'nlp_research',
                'metadata': {
                    'name': 'Sentiment Analysis Model',
                    'description': 'BERT-based model fine-tuned for social media sentiment analysis',
                    'category': 'Natural Language Processing',
                    'framework': 'PyTorch',
                    'model_type': 'Transformer (BERT)',
                    'accuracy': '91.8%',
                    'parameters': '110M',
                    'input_size': 'Variable text',
                    'tags': ['bert', 'sentiment', 'nlp', 'social-media', 'pytorch'],
                    'training_dataset': 'Twitter Sentiment + Reviews',
                    'last_updated': '2025-05-17'
                },
                'price': 149.99
            },
            {
                'owner': 'auto_ml_systems',
                'metadata': {
                    'name': 'Fraud Detection Model',
                    'description': 'XGBoost model for real-time credit card fraud detection',
                    'category': 'Finance',
                    'framework': 'XGBoost',
                    'model_type': 'Gradient Boosting',
                    'accuracy': '98.7%',
                    'parameters': '50K',
                    'input_size': '30 features',
                    'tags': ['fraud-detection', 'xgboost', 'finance', 'real-time'],
                    'training_dataset': 'Credit Card Transactions',
                    'last_updated': '2025-05-20'
                },
                'price': 499.99
            }
        ]

        # Füge Datensätze zur Blockchain hinzu
        for dataset in demo_datasets:
            try:
                blockchain.data_upload_transaction(
                    dataset['owner'],
                    dataset['metadata'],
                    dataset['price']
                )
            except Exception as e:
                print(f"Fehler beim Hinzufügen von Dataset: {e}")

        # Füge Modelle zur Blockchain hinzu
        for model in demo_models:
            try:
                blockchain.model_upload_transaction(
                    model['owner'],
                    model['metadata'],
                    model['price']
                )
            except Exception as e:
                print(f"Fehler beim Hinzufügen von Model: {e}")

        # Mine einen Block mit den neuen Transaktionen
        if blockchain.current_transactions:
            try:
                new_block, mining_time = blockchain.mine_block(difficulty=2)
                print(f"Demo-Daten in Block {new_block.index} gemined (Zeit: {mining_time:.2f}s)")
            except Exception as e:
                print(f"Fehler beim Minen des Demo-Blocks: {e}")


# Marketplace Haupt-Route
@app.route('/marketplace')
def marketplace():
    """Hauptseite des Marketplaces mit allen verfügbaren Daten und Modellen"""

    # Initialisiere Demo-Daten falls nötig
    initialize_demo_marketplace_data()

    try:
        # Filter-Parameter aus URL
        category_filter = request.args.get('category', '')
        item_type = request.args.get('type', 'all')  # all, data, models
        search_query = request.args.get('search', '')
        sort_by = request.args.get('sort', 'newest')  # newest, oldest, price_low, price_high, name
        price_min = request.args.get('price_min', type=float)
        price_max = request.args.get('price_max', type=float)

        # Extrahiere alle Marketplace-Items aus der Blockchain
        all_items = []

        # Durchsuche alle Blöcke nach Upload-Transaktionen
        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.get('type') in ['data_upload', 'model_upload']:
                    try:
                        # Bereite Item-Daten für Anzeige auf
                        item = {
                            'id': tx.get('transaction_id'),
                            'type': 'dataset' if tx.get('type') == 'data_upload' else 'model',
                            'owner': tx.get('owner', 'Unknown'),
                            'price': tx.get('price', 0),
                            'metadata': tx.get('metadata', {}),
                            'block_index': block.index,
                            'timestamp': tx.get('timestamp', block.timestamp),
                            'formatted_date': datetime.fromtimestamp(tx.get('timestamp', block.timestamp)).strftime(
                                "%d.%m.%Y")
                        }

                        # Erweitere Metadaten für bessere Anzeige
                        metadata = item['metadata']
                        item.update({
                            'name': metadata.get('name', 'Unnamed Item'),
                            'description': metadata.get('description', 'No description available'),
                            'category': metadata.get('category', 'Uncategorized'),
                            'tags': metadata.get('tags', []),
                            'quality_score': metadata.get('quality_score', 0),
                            'size': metadata.get('size', 'Unknown'),
                            'format': metadata.get('format', 'Unknown')
                        })

                        # Typ-spezifische Felder
                        if item['type'] == 'dataset':
                            item.update({
                                'samples': metadata.get('samples', 0),
                                'features': metadata.get('features', 0)
                            })
                        else:  # model
                            item.update({
                                'framework': metadata.get('framework', 'Unknown'),
                                'accuracy': metadata.get('accuracy', 'N/A'),
                                'model_type': metadata.get('model_type', 'Unknown')
                            })

                        all_items.append(item)

                    except Exception as e:
                        print(f"Fehler beim Verarbeiten von Item {tx.get('transaction_id', 'Unknown')}: {e}")
                        continue

        # Anwenden der Filter
        filtered_items = all_items.copy()

        # Typ-Filter
        if item_type == 'data':
            filtered_items = [item for item in filtered_items if item['type'] == 'dataset']
        elif item_type == 'models':
            filtered_items = [item for item in filtered_items if item['type'] == 'model']

        # Kategorie-Filter
        if category_filter:
            filtered_items = [item for item in filtered_items if item['category'].lower() == category_filter.lower()]

        # Such-Filter
        if search_query:
            search_lower = search_query.lower()
            filtered_items = [
                item for item in filtered_items
                if search_lower in item['name'].lower()
                   or search_lower in item['description'].lower()
                   or any(search_lower in tag.lower() for tag in item['tags'])
            ]

        # Preis-Filter
        if price_min is not None:
            filtered_items = [item for item in filtered_items if item['price'] >= price_min]
        if price_max is not None:
            filtered_items = [item for item in filtered_items if item['price'] <= price_max]

        # Sortierung
        if sort_by == 'newest':
            filtered_items.sort(key=lambda x: x['timestamp'], reverse=True)
        elif sort_by == 'oldest':
            filtered_items.sort(key=lambda x: x['timestamp'])
        elif sort_by == 'price_low':
            filtered_items.sort(key=lambda x: x['price'])
        elif sort_by == 'price_high':
            filtered_items.sort(key=lambda x: x['price'], reverse=True)
        elif sort_by == 'name':
            filtered_items.sort(key=lambda x: x['name'].lower())

        # Statistiken für Sidebar
        stats = {
            'total_items': len(all_items),
            'datasets': len([item for item in all_items if item['type'] == 'dataset']),
            'models': len([item for item in all_items if item['type'] == 'model']),
            'categories': list(set(item['category'] for item in all_items)),
            'filtered_count': len(filtered_items),
            'avg_price': sum(item['price'] for item in all_items) / len(all_items) if all_items else 0,
            'price_range': {
                'min': min(item['price'] for item in all_items) if all_items else 0,
                'max': max(item['price'] for item in all_items) if all_items else 0
            }
        }

        # Template-Variablen
        template_vars = {
            'items': filtered_items,
            'stats': stats,
            'filters': {
                'category': category_filter,
                'type': item_type,
                'search': search_query,
                'sort': sort_by,
                'price_min': price_min,
                'price_max': price_max
            }
        }

        return render_template('marketplace.html', **template_vars)

    except Exception as e:
        flash(f'Fehler beim Laden des Marketplaces: {str(e)}', 'danger')
        return redirect(url_for('index'))


# Item-Detail Route
@app.route('/marketplace/item/<item_id>')
def marketplace_item_details(item_id):
    """Detailansicht für ein einzelnes Marketplace-Item"""

    try:
        # Suche das Item in der Blockchain
        found_item = None
        found_block = None

        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.get('transaction_id') == item_id and tx.get('type') in ['data_upload', 'model_upload']:
                    found_item = tx
                    found_block = block
                    break
            if found_item:
                break

        if not found_item:
            flash(f'Item mit ID {item_id} wurde nicht gefunden.', 'warning')
            return redirect(url_for('marketplace'))

        # Bereite Item-Details auf
        item_type = 'dataset' if found_item.get('type') == 'data_upload' else 'model'
        metadata = found_item.get('metadata', {})

        item_details = {
            'id': found_item.get('transaction_id'),
            'type': item_type,
            'owner': found_item.get('owner', 'Unknown'),
            'price': found_item.get('price', 0),
            'metadata': metadata,
            'block_index': found_block.index,
            'timestamp': found_item.get('timestamp', found_block.timestamp),
            'formatted_date': datetime.fromtimestamp(found_item.get('timestamp', found_block.timestamp)).strftime(
                "%d.%m.%Y um %H:%M"),
            'blockchain_verified': True
        }

        # Erweiterte Metadaten
        item_details.update({
            'name': metadata.get('name', 'Unnamed Item'),
            'description': metadata.get('description', 'No description available'),
            'category': metadata.get('category', 'Uncategorized'),
            'tags': metadata.get('tags', []),
            'quality_score': metadata.get('quality_score', 0),
            'size': metadata.get('size', 'Unknown'),
            'format': metadata.get('format', 'Unknown'),
            'last_updated': metadata.get('last_updated', 'Unknown')
        })

        # Typ-spezifische Details
        if item_type == 'dataset':
            item_details.update({
                'samples': metadata.get('samples', 0),
                'features': metadata.get('features', 0)
            })
        else:  # model
            item_details.update({
                'framework': metadata.get('framework', 'Unknown'),
                'accuracy': metadata.get('accuracy', 'N/A'),
                'model_type': metadata.get('model_type', 'Unknown'),
                'parameters': metadata.get('parameters', 'Unknown'),
                'input_size': metadata.get('input_size', 'Unknown'),
                'training_dataset': metadata.get('training_dataset', 'Unknown')
            })

        # Prüfe ob aktueller Benutzer bereits Besitzer ist
        current_user_address = session.get('blockchain_address', '')
        is_owner = current_user_address == item_details['owner']
        has_purchased = False  # TODO: Implementiere Purchase-Check

        # Ähnliche Items finden
        similar_items = []
        item_category = item_details['category']

        for block in blockchain.chain:
            for tx in block.transactions:
                if (tx.get('type') in ['data_upload', 'model_upload']
                        and tx.get('transaction_id') != item_id
                        and tx.get('metadata', {}).get('category') == item_category):

                    similar_item = {
                        'id': tx.get('transaction_id'),
                        'name': tx.get('metadata', {}).get('name', 'Unnamed'),
                        'price': tx.get('price', 0),
                        'type': 'dataset' if tx.get('type') == 'data_upload' else 'model'
                    }
                    similar_items.append(similar_item)

                    if len(similar_items) >= 3:  # Max 3 ähnliche Items
                        break
            if len(similar_items) >= 3:
                break

        return render_template('marketplace_item_details.html',
                               item=item_details,
                               is_owner=is_owner,
                               has_purchased=has_purchased,
                               similar_items=similar_items)

    except Exception as e:
        flash(f'Fehler beim Laden der Item-Details: {str(e)}', 'danger')
        return redirect(url_for('marketplace'))


# Purchase Route
@app.route('/marketplace/purchase', methods=['POST'])
@login_required
def marketplace_purchase():
    """Verarbeitet Käufe von Marketplace-Items"""

    try:
        item_id = request.form.get('item_id')
        buyer_address = session.get('blockchain_address')

        if not item_id:
            flash('Keine Item-ID angegeben.', 'danger')
            return redirect(url_for('marketplace'))

        # Suche das Item
        found_item = None
        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.get('transaction_id') == item_id:
                    found_item = tx
                    break
            if found_item:
                break

        if not found_item:
            flash('Item nicht gefunden.', 'danger')
            return redirect(url_for('marketplace'))

        # Prüfe ob Benutzer bereits Besitzer ist
        if found_item.get('owner') == buyer_address:
            flash('Du kannst deine eigenen Items nicht kaufen.', 'warning')
            return redirect(url_for('marketplace_item_details', item_id=item_id))

        # Erstelle Purchase-Transaktion
        item_type = found_item.get('type')
        item_price = found_item.get('price', 0)

        if item_type == 'data_upload':
            transaction_id = blockchain.data_purchase_transaction(
                buyer_address, item_id, item_price
            )
        elif item_type == 'model_upload':
            transaction_id = blockchain.model_purchase_transaction(
                buyer_address, item_id, item_price
            )
        else:
            flash('Ungültiger Item-Typ.', 'danger')
            return redirect(url_for('marketplace_item_details', item_id=item_id))

        flash(f'Kauf erfolgreich! Transaktion {transaction_id[:16]}... wurde erstellt und wartet auf Mining.',
              'success')
        return redirect(url_for('marketplace_item_details', item_id=item_id))

    except Exception as e:
        flash(f'Fehler beim Kauf: {str(e)}', 'danger')
        return redirect(url_for('marketplace'))


# User Dashboard Route
@app.route('/marketplace/dashboard')
@login_required
def marketplace_dashboard():
    """Dashboard für Benutzer mit eigenen und gekauften Items"""

    try:
        user_address = session.get('blockchain_address')

        # Sammle Benutzer-Items
        owned_items = []
        purchased_items = []

        for block in blockchain.chain:
            for tx in block.transactions:
                # Eigene Uploads
                if (tx.get('type') in ['data_upload', 'model_upload']
                        and tx.get('owner') == user_address):

                    item = {
                        'id': tx.get('transaction_id'),
                        'name': tx.get('metadata', {}).get('name', 'Unnamed'),
                        'type': 'dataset' if tx.get('type') == 'data_upload' else 'model',
                        'price': tx.get('price', 0),
                        'upload_date': datetime.fromtimestamp(tx.get('timestamp', block.timestamp)).strftime(
                            "%d.%m.%Y"),
                        'block_index': block.index
                    }
                    owned_items.append(item)

                # Gekaufte Items
                elif (tx.get('type') in ['data_purchase', 'model_purchase']
                      and tx.get('buyer') == user_address):

                    item_id = tx.get('data_id') or tx.get('model_id')
                    purchase_item = {
                        'id': item_id,
                        'transaction_id': tx.get('transaction_id'),
                        'type': 'dataset' if tx.get('type') == 'data_purchase' else 'model',
                        'amount': tx.get('amount', 0),
                        'purchase_date': datetime.fromtimestamp(tx.get('timestamp', block.timestamp)).strftime(
                            "%d.%m.%Y"),
                        'seller': tx.get('seller', 'Unknown'),
                        'block_index': block.index
                    }

                    # Finde Original-Item für Namen
                    for search_block in blockchain.chain:
                        for search_tx in search_block.transactions:
                            if search_tx.get('transaction_id') == item_id:
                                purchase_item['name'] = search_tx.get('metadata', {}).get('name', 'Unnamed')
                                break

                    purchased_items.append(purchase_item)

        # Statistiken
        dashboard_stats = {
            'owned_count': len(owned_items),
            'purchased_count': len(purchased_items),
            'total_earned': sum(item['price'] for item in owned_items),
            'total_spent': sum(item['amount'] for item in purchased_items)
        }

        return render_template('marketplace_dashboard.html',
                               owned_items=owned_items,
                               purchased_items=purchased_items,
                               stats=dashboard_stats)

    except Exception as e:
        flash(f'Fehler beim Laden des Dashboards: {str(e)}', 'danger')
        return redirect(url_for('marketplace'))


# API-Endpunkt für Marketplace-Statistiken
@app.route('/api/marketplace/stats')
def marketplace_stats_api():
    """JSON-API für Marketplace-Statistiken"""

    try:
        # Sammle alle Items
        all_items = []

        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.get('type') in ['data_upload', 'model_upload']:
                    all_items.append({
                        'type': 'dataset' if tx.get('type') == 'data_upload' else 'model',
                        'price': tx.get('price', 0),
                        'category': tx.get('metadata', {}).get('category', 'Unknown')
                    })

        # Berechne Statistiken
        stats = {
            'total_items': len(all_items),
            'datasets': len([item for item in all_items if item['type'] == 'dataset']),
            'models': len([item for item in all_items if item['type'] == 'model']),
            'avg_price': sum(item['price'] for item in all_items) / len(all_items) if all_items else 0,
            'categories': list(set(item['category'] for item in all_items)),
            'last_update': time.time()
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)