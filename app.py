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
import os
from werkzeug.utils import secure_filename
from marketplace import MarketplaceBlockchain
from flask import send_file
import io
import json
from database import User
from database_handling import reset_database
from database import DatabaseManager
# Flask App Initialisierung
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'entwicklungsschluessel')

# Blockchain Instanz erstellen

blockchain = MarketplaceBlockchain()

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
            blockchain_address = session.get('blockchain_address')

            if username and blockchain_address:
                return {
                    'username': username,
                    'blockchain_address': blockchain_address
                }
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
    """Login-Funktion mit Datenbank-Integration"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'

        if not username or not password:
            flash('Bitte fülle alle Felder aus.', 'danger')
            return render_template('login.html')

        # Lade users.json für Login-Daten
        users = load_users()

        if username in users:
            stored_password_hash = users[username]['password_hash']
            input_password_hash = hash_password(password)

            if stored_password_hash == input_password_hash:
                blockchain_address = users[username]['blockchain_address']

                # Stelle sicher, dass User in der Datenbank existiert
                session_db = blockchain.db_manager.get_session()
                try:
                    user = session_db.query(User).filter_by(address=blockchain_address).first()

                    if not user:
                        # User existiert nicht in DB → registriere ihn
                        print(f"Registriere User {username} in Datenbank...")
                        user = blockchain.register_user(blockchain_address)
                        print(f"User registriert: {blockchain_address}")

                    # Session setzen
                    session['username'] = username
                    session['blockchain_address'] = blockchain_address

                    if remember_me:
                        session.permanent = True

                    flash(f'Willkommen zurück, {username}!', 'success')
                    return redirect(url_for('index'))

                finally:
                    session_db.close()
            else:
                flash('Ungültiger Benutzername oder Passwort.', 'danger')
        else:
            flash('Ungültiger Benutzername oder Passwort.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register-Funktion mit Datenbank-Integration"""
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

        # Lade bestehende User
        users = load_users()

        # Prüfe ob Username bereits existiert
        if username in users:
            flash('Dieser Benutzername ist bereits vergeben.', 'danger')
            return render_template('register.html')

        try:
            # Generiere neue Blockchain-Adresse
            blockchain_address = str(uuid.uuid4()).replace('-', '')
            password_hash = hash_password(password)

            # Speichere in users.json
            users[username] = {
                "username": username,
                "password_hash": password_hash,
                "blockchain_address": blockchain_address
            }
            save_users(users)

            # Registriere User in der Datenbank
            user = blockchain.register_user(blockchain_address)

            # Automatisch einloggen
            session['username'] = username
            session['blockchain_address'] = blockchain_address

            flash('Dein Konto wurde erfolgreich erstellt!', 'success')
            print(f"Neuer User registriert: {username} → {blockchain_address}")

            return redirect(url_for('index'))

        except Exception as e:
            flash(f'Fehler bei der Registrierung: {str(e)}', 'danger')
            print(f"Registrierungsfehler: {str(e)}")
            return render_template('register.html')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('blockchain_address', None)
    flash('Du wurdest erfolgreich abgemeldet.', 'success')
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
            # KORRIGIERT: Verwende die gespeicherte Mining-Zeit aus dem Block
            if hasattr(block, 'mining_time') and block.mining_time > 0:
                block_details['mining_time'] = f"{block.mining_time:.2f} seconds"
            else:
                # Fallback für alte Blöcke ohne mining_time
                previous_block = blockchain.chain[block_index - 1]
                time_since_previous = block.timestamp - previous_block.timestamp
                block_details['mining_time'] = f"{time_since_previous:.2f} seconds (estimated)"
        else:
            block_details['mining_time'] = "Genesis Block"

        # Proof-of-Work Verification - USE STORED DIFFICULTY
        if block_index > 0:
            last_proof = blockchain.chain[block_index - 1].proof
            current_proof = block.proof
            stored_difficulty = getattr(block, 'difficulty', 4)  # Use stored difficulty or default to 4

            guess = f"{last_proof}{current_proof}".encode()
            guess_hash = hashlib.sha256(guess).hexdigest()

            block_details['pow_verification'] = {
                'last_proof': last_proof,
                'current_proof': current_proof,
                'combined_hash': guess_hash,
                'leading_zeros': len(guess_hash) - len(guess_hash.lstrip('0')),
                'difficulty_used': stored_difficulty,  # Show the actual difficulty used
                'target_zeros': '0' * stored_difficulty,  # Show the target pattern
                'is_valid': guess_hash.startswith('0' * stored_difficulty)  # Validate with correct difficulty
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


# MARKETPLACE
def initialize_demo_marketplace_data():
    """Prüft ob die Blockchain bereit ist"""

    # Einfache Prüfung ob Blockchain initialisiert ist
    if len(blockchain.chain) == 0:
        print("Blockchain nicht initialisiert - erstelle Genesis-Block")
        blockchain.create_genesis_block()
    else:
        print(f"Blockchain bereit mit {len(blockchain.chain)} Block(s)")

    # Keine Demo-Daten mehr erstellen
    print("Demo-Daten-Erstellung übersprungen - nur echte User-Uploads werden verarbeitet")


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
    """Verarbeitet Käufe von Marketplace-Items - KORRIGIERT für Schlüssel-Übertragung"""

    try:
        item_id = request.form.get('item_id')
        buyer_address = session.get('blockchain_address')

        if not item_id:
            flash('Keine Item-ID angegeben.', 'danger')
            return redirect(url_for('marketplace'))

        print(f"DEBUG Purchase: Käufer {buyer_address} kauft Item {item_id}")

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

        # Prüfe ob User bereits gekauft hat
        already_purchased = check_download_permission(buyer_address, item_id)
        if already_purchased:
            flash('Du hast dieses Item bereits gekauft.', 'info')
            return redirect(url_for('marketplace_item_details', item_id=item_id))

        # Erstelle Purchase-Transaktion
        item_type = found_item.get('type')
        item_price = found_item.get('price', 0)

        print(f"DEBUG Purchase: Item-Typ: {item_type}, Preis: {item_price}")

        # NEU: Lade Owner-Schlüssel BEVOR der Kauf abgeschlossen wird
        owner_encryption_key = load_encryption_key(item_id, None)  # Owner-Schlüssel laden
        if not owner_encryption_key:
            flash('Verschlüsselungsschlüssel für dieses Item nicht verfügbar.', 'danger')
            return redirect(url_for('marketplace_item_details', item_id=item_id))

        print(f"DEBUG Purchase: Owner-Schlüssel gefunden: {owner_encryption_key[:20]}...")

        # Erstelle Purchase-Transaktion
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

        print(f"DEBUG Purchase: Transaktion erstellt: {transaction_id}")

        # Speichere Schlüssel für den Käufer
        try:
            save_key_for_buyer(buyer_address, item_id, owner_encryption_key, found_item)
            print(f"DEBUG Purchase: Schlüssel für Käufer {buyer_address} gespeichert")
        except Exception as key_error:
            print(f"ERROR Purchase: Schlüssel-Speicherung fehlgeschlagen: {key_error}")
            # Kauf trotzdem durchführen, aber warnen
            flash('Kauf erfolgreich, aber Schlüssel-Zugang könnte verzögert sein.', 'warning')

        flash(f'Kauf erfolgreich! Transaktion {transaction_id[:16]}... wurde erstellt und wartet auf Mining.',
              'success')
        flash('Du kannst das Item nach dem Mining herunterladen.', 'info')

        return redirect(url_for('my_purchases'))

    except Exception as e:
        print(f"ERROR Purchase: {str(e)}")
        flash(f'Fehler beim Kauf: {str(e)}', 'danger')
        return redirect(url_for('marketplace'))


def save_key_for_buyer(buyer_address, item_id, encryption_key, original_item):
    """Speichert den Verschlüsselungsschlüssel für den Käufer"""

    print(f"DEBUG save_key_for_buyer: buyer={buyer_address}, item={item_id}")

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

    # Bestimme den Namen des Items
    item_name = 'Unknown Item'
    if original_item:
        metadata = original_item.get('metadata', {})
        item_name = metadata.get('name', 'Unknown Item')

    # Füge Eintrag für den Käufer hinzu (mit purchased_by-Flag)
    buyer_key_entry = {
        "name": item_name,
        "data_id": item_id,
        "encryption_key": encryption_key,
        "upload_date": datetime.now().strftime('%Y-%m-%d'),
        "purchased_by": buyer_address,  # WICHTIG: Markiere als gekauft
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
    else:
        print(f"Schlüssel für Käufer {buyer_address} bereits vorhanden")


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


# Upload-Konfiguration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    'dataset': {'csv', 'json', 'xlsx', 'xls', 'zip', 'jpg', 'jpeg', 'png', 'parquet'},
    'model': {'pkl', 'h5', 'onnx', 'pt', 'pth', 'zip', 'joblib'}
}

# Stelle sicher, dass Upload-Ordner existiert
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename, upload_type):
    """Prüft ob Dateiendung erlaubt ist"""
    if '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS.get(upload_type, set())


def get_file_size_mb(file_path):
    """Gibt Dateigröße in MB zurück"""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)

# Upload-Route für Datasets und Modelle
@app.route('/upload-dataset', methods=['GET', 'POST'])
@login_required
def upload_dataset():
    """Upload-Seite für Datasets und Modelle mit korrigierter Verschlüsselung"""

    if request.method == 'GET':
        return render_template('upload_dataset.html')

    try:
        # Form-Daten extrahieren
        upload_type = request.form.get('upload_type', 'dataset')
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        price = float(request.form.get('price', 0))
        tags_str = request.form.get('tags', '')

        # Tags verarbeiten
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []

        # Validierung
        if not name:
            flash('Bitte gib einen Namen für deinen Upload an.', 'danger')
            return redirect(url_for('upload_dataset'))

        if not category:
            flash('Bitte wähle eine Kategorie aus.', 'danger')
            return redirect(url_for('upload_dataset'))

        if not description:
            flash('Bitte füge eine Beschreibung hinzu.', 'danger')
            return redirect(url_for('upload_dataset'))

        if price < 0:
            flash('Der Preis kann nicht negativ sein.', 'danger')
            return redirect(url_for('upload_dataset'))

        # Datei-Upload prüfen
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt.', 'danger')
            return redirect(url_for('upload_dataset'))

        file = request.files['file']
        if file.filename == '':
            flash('Keine Datei ausgewählt.', 'danger')
            return redirect(url_for('upload_dataset'))

        # Datei-Validierung
        if not allowed_file(file.filename, upload_type):
            allowed_exts = ', '.join(ALLOWED_EXTENSIONS[upload_type])
            flash(f'Dateityp nicht erlaubt. Erlaubte Formate: {allowed_exts}', 'danger')
            return redirect(url_for('upload_dataset'))

        # Sichere Dateinamen
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        # Datei temporär speichern
        file.save(file_path)

        # Dateigröße prüfen
        file_size_mb = get_file_size_mb(file_path)
        if file_size_mb > 100:  # 100MB Limit
            os.remove(file_path)
            flash('Datei zu groß. Maximum: 100MB', 'danger')
            return redirect(url_for('upload_dataset'))

        # Metadaten vorbereiten
        metadata = {
            'name': name,
            'description': description,
            'category': category,
            'tags': tags,
            'format': request.form.get('format', ''),
            'size': f"{file_size_mb} MB",
            'original_filename': filename,
            'upload_date': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }

        # Typ-spezifische Metadaten
        if upload_type == 'dataset':
            samples = request.form.get('samples', type=int)
            features = request.form.get('features', type=int)

            if samples:
                metadata['samples'] = samples
            if features:
                metadata['features'] = features

        elif upload_type == 'model':
            framework = request.form.get('framework', '').strip()
            model_type = request.form.get('model_type', '').strip()
            accuracy = request.form.get('accuracy', '').strip()
            parameters = request.form.get('parameters', '').strip()
            training_dataset = request.form.get('training_dataset', '').strip()

            if framework:
                metadata['framework'] = framework
            if model_type:
                metadata['model_type'] = model_type
            if accuracy:
                metadata['accuracy'] = accuracy
            if parameters:
                metadata['parameters'] = parameters
            if training_dataset:
                metadata['training_dataset'] = training_dataset

        # Benutzer-Adresse
        owner_address = session.get('blockchain_address')
        if not owner_address:
            os.remove(file_path)
            flash('Keine gültige Blockchain-Adresse gefunden. Bitte logge dich erneut ein.', 'danger')
            return redirect(url_for('login'))

        # WICHTIG: Datei lesen für Verschlüsselung
        print(f"DEBUG Upload: Lese Datei {file_path} für Verschlüsselung...")
        with open(file_path, 'rb') as f:
            file_content = f.read()

        print(f"DEBUG Upload: Datei gelesen, {len(file_content)} Bytes")

        # Zu Blockchain hinzufügen MIT VERSCHLÜSSELUNG
        try:
            if upload_type == 'dataset':
                # KORRIGIERT: Verwende upload_data_with_file für automatische Verschlüsselung
                print(f"DEBUG Upload: Verwende upload_data_with_file für Dataset...")
                data_id, encryption_key = blockchain.upload_data_with_file(
                    owner_address, file_content, metadata, price
                )
                upload_id = data_id
                print(f"DEBUG Upload: Dataset hochgeladen - ID: {data_id}, Key: {encryption_key[:20]}...")

            else:  # model
                # KORRIGIERT: upload_model_with_file für automatische Verschlüsselung
                print(f"DEBUG Upload: Verwende upload_model_with_file für Model...")
                model_id, encryption_key = blockchain.upload_model_with_file(
                    owner_address, file_content, metadata, price
                )
                upload_id = model_id
                print(f"DEBUG Upload: Model hochgeladen - ID: {model_id}, Key: {encryption_key[:20]}...")

            # Jetzt erst lokale Datei löschen (nach erfolgreichem Upload)
            os.remove(file_path)
            print(f"DEBUG Upload: Lokale Datei {file_path} gelöscht")

            # Erfolgsmeldung mit Hinweis auf Mining
            item_type = "Dataset" if upload_type == 'dataset' else "Modell"
            pending_count = len(blockchain.current_transactions)

            flash(f'Die Transaktion wartet jetzt auf Mining. Es sind {pending_count} Transaktionen ausstehend.', 'info')
            flash(f'Verschlüsselungsschlüssel wurde sicher gespeichert.', 'info')

            # Weiterleitung zum Marketplace (Item ist noch nicht verfügbar bis gemined --> kann vom user selbst gemined werden)
            return redirect(url_for('marketplace'))

        except Exception as blockchain_error:
            # Bei Blockchain-Fehler: Datei löschen und Fehler melden
            if os.path.exists(file_path):
                os.remove(file_path)

            print(f"ERROR Upload: Blockchain-Fehler: {str(blockchain_error)}")
            flash(f'Fehler beim Hinzufügen zur Blockchain: {str(blockchain_error)}', 'danger')
            return redirect(url_for('upload_dataset'))

    except ValueError as e:
        # Datei aufräumen bei Validierungsfehlern
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        flash(f'Ungültige Eingabe: {str(e)}', 'danger')
        return redirect(url_for('upload_dataset'))

    except Exception as e:
        # Datei aufräumen bei allgemeinen Fehlern
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        print(f"ERROR Upload: Allgemeiner Fehler: {str(e)}")
        flash(f'Upload-Fehler: {str(e)}', 'danger')
        return redirect(url_for('upload_dataset'))




@app.route('/api/upload/status/<upload_id>')
@login_required
def upload_status(upload_id):
    """API-Endpunkt für Upload-Status-Updates"""
    try:
        # Weis noch nicht ob ich das brauche.

        return jsonify({
            'status': 'completed',
            'message': 'Upload erfolgreich verarbeitet',
            'item_id': upload_id
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Mine automatisch einen Block nach Upload (optional)
@app.route('/api/mine-block', methods=['POST'])
@login_required
def mine_block_api():
    """Mined einen neuen Block mit ausstehenden Transaktionen"""
    try:
        if len(blockchain.current_transactions) == 0:
            return jsonify({'error': 'Keine ausstehenden Transaktionen'}), 400

        # Mine Block mit niedriger Schwierigkeit für Demo
        new_block, mining_time = blockchain.mine_block(difficulty=2)

        return jsonify({
            'success': True,
            'block_index': new_block.index,
            'mining_time': f"{mining_time:.2f} seconds",
            'transactions_count': len(new_block.transactions)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/debug/blockchain')
@login_required
def debug_blockchain():
    """Debug-Route um Blockchain-Inhalt zu prüfen"""
    debug_info = {
        'total_blocks': len(blockchain.chain),
        'transactions_per_block': [],
        'all_transaction_ids': []
    }

    for i, block in enumerate(blockchain.chain):
        block_info = {
            'block_index': i,
            'transaction_count': len(block.transactions),
            'transactions': []
        }

        for tx in block.transactions:
            tx_info = {
                'id': tx.get('transaction_id', 'NO_ID'),
                'type': tx.get('type', 'NO_TYPE'),
                'owner': tx.get('owner', 'NO_OWNER')
            }
            block_info['transactions'].append(tx_info)
            debug_info['all_transaction_ids'].append(tx.get('transaction_id'))

        debug_info['transactions_per_block'].append(block_info)

    return jsonify(debug_info)


@app.route('/mine')
@login_required
def mine_page():
    """Mining-Seite mit Live-Animation"""

    # Prüfe ob Transaktionen zum Minen vorhanden sind
    pending_count = len(blockchain.current_transactions)

    if pending_count == 0:
        flash('Keine ausstehenden Transaktionen zum Minen verfügbar.', 'info')
        return redirect(url_for('blockchain_explorer'))

    # Bereite Mining-Informationen vor
    mining_info = {
        'pending_transactions': pending_count,
        'last_block_hash': blockchain.last_block.hash,
        'last_proof': blockchain.last_block.proof,
        'difficulty': 4,  # Standard Schwierigkeit
        'target_zeros': '0000',  # Für Difficulty 4
        'next_block_index': len(blockchain.chain)
    }

    # Beispiel der aktuellen Transaktionen für Anzeige
    pending_transactions = []
    for i, tx in enumerate(blockchain.current_transactions[:5]):  # Zeige max 5
        tx_display = {
            'index': i + 1,
            'type': tx.get('type', 'transfer'),
            'from': tx.get('owner') or tx.get('sender', 'Unknown'),
            'amount': tx.get('price') or tx.get('amount', 0),
            'name': tx.get('metadata', {}).get('name') if tx.get('metadata') else tx.get('transaction_id', '')[
                                                                                  :16] + '...'
        }
        pending_transactions.append(tx_display)

    return render_template('mining.html',
                           mining_info=mining_info,
                           pending_transactions=pending_transactions)


@app.route('/api/mine/simulate', methods=['POST'])
@login_required
def simulate_mining():
    """API-Endpunkt für Live-Mining-Simulation"""

    try:
        data = request.json
        last_proof = data.get('last_proof', blockchain.last_block.proof)
        current_attempt = data.get('current_attempt', 0)
        difficulty = data.get('difficulty', 4)

        # Berechne Hash für aktuellen Versuch - verwende echte Blockchain-Logik
        guess = f"{last_proof}{current_attempt}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        # Prüfe ob gültig mit der echten valid_proof Methode
        is_valid = blockchain.valid_proof(last_proof, current_attempt, difficulty)

        # Zähle führende Nullen
        leading_zeros = len(guess_hash) - len(guess_hash.lstrip('0'))

        return jsonify({
            'attempt': current_attempt,
            'hash': guess_hash,
            'is_valid': is_valid,
            'leading_zeros': leading_zeros,
            'target_zeros': difficulty,
            'difficulty': difficulty,
            'attempts_per_second': 1000  # Simulierte Geschwindigkeit
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mine/start', methods=['POST'])
@login_required
def start_mining():
    """API-Endpunkt um echtes Mining zu starten"""

    try:
        if len(blockchain.current_transactions) == 0:
            return jsonify({'error': 'Keine ausstehenden Transaktionen'}), 400

        # Mining-Parameter aus Request
        difficulty = int(request.json.get('difficulty', 4))

        print(f"\n=== API MINING START DEBUG ===")
        print(f"Difficulty: {difficulty}")

        # Verwende die echte mine_block Methode
        new_block, mining_time = blockchain.mine_block(difficulty)

        print(f"API: Zurückgegebene Mining-Zeit: {mining_time:.6f}")
        print(f"API: Block Mining-Zeit Attribut: {new_block.mining_time:.6f}")
        print(f"=== API MINING DEBUG ENDE ===\n")

        return jsonify({
            'success': True,
            'block_index': new_block.index,
            'proof': new_block.proof,
            'hash': new_block.hash,
            'mining_time': mining_time,
            'block_mining_time': new_block.mining_time,  # NEW: Also return block's mining time
            'transactions_mined': len(new_block.transactions),
            'difficulty': difficulty
        })

    except Exception as e:
        print(f"ERROR in start_mining API: {str(e)}")
        return jsonify({'error': str(e)}), 500


#EINKAEUFE EINSEHEN

# Route für "Meine Käufe" Dashboard
@app.route('/marketplace/my-purchases')
@login_required
def my_purchases():
    """Dashboard für gekaufte Items mit korrigierter ID-Logik"""

    try:
        user_address = session.get('blockchain_address')

        purchased_items = []
        pending_purchases = []

        # 1. Suche in der Blockchain nach bestätigten Käufen
        for block in blockchain.chain:
            for tx in block.transactions:
                if (tx.get('type') in ['data_purchase', 'model_purchase']
                        and tx.get('buyer') == user_address):
                    # WICHTIG: item_id ist die ORIGINAL Upload-Transaction-ID
                    original_item_id = tx.get('data_id') or tx.get('model_id')

                    print(f"DEBUG: Gefundener Kauf - Original Item ID: {original_item_id}")

                    # Suche Original-Upload für Details
                    original_item = find_original_item(original_item_id)

                    purchased_item = {
                        'purchase_tx_id': tx.get('transaction_id'),  # Purchase-Transaction-ID
                        'item_id': original_item_id,  # ORIGINAL Upload-Transaction-ID für Download
                        'item_name': original_item.get('name', 'Unknown') if original_item else 'Unknown',
                        'item_type': 'Dataset' if tx.get('type') == 'data_purchase' else 'Model',
                        'purchase_amount': tx.get('amount', 0),
                        'purchase_date': datetime.fromtimestamp(tx.get('timestamp', block.timestamp)).strftime(
                            "%d.%m.%Y %H:%M"),
                        'block_index': block.index,
                        'seller': tx.get('seller', 'Unknown'),
                        'status': 'confirmed',
                        'can_download': True,
                        'original_metadata': original_item.get('metadata', {}) if original_item else {}
                    }
                    purchased_items.append(purchased_item)

        # 2. Suche in Pending Transactions nach wartenden Käufen
        for tx in blockchain.current_transactions:
            if (tx.get('type') in ['data_purchase', 'model_purchase']
                    and tx.get('buyer') == user_address):
                original_item_id = tx.get('data_id') or tx.get('model_id')
                original_item = find_original_item(original_item_id)

                pending_item = {
                    'purchase_tx_id': tx.get('transaction_id'),
                    'item_id': original_item_id,  # Auch hier: Original Item ID
                    'item_name': original_item.get('name', 'Unknown') if original_item else 'Unknown',
                    'item_type': 'Dataset' if tx.get('type') == 'data_purchase' else 'Model',
                    'purchase_amount': tx.get('amount', 0),
                    'purchase_date': datetime.fromtimestamp(tx.get('timestamp', time.time())).strftime(
                        "%d.%m.%Y %H:%M"),
                    'block_index': 'Pending',
                    'seller': tx.get('seller', 'Unknown'),
                    'status': 'pending',
                    'can_download': False,
                    'original_metadata': original_item.get('metadata', {}) if original_item else {}
                }
                pending_purchases.append(pending_item)

        # Nach Datum sortieren
        all_purchases = pending_purchases + purchased_items
        all_purchases.sort(key=lambda x: x['purchase_date'], reverse=True)

        # Statistiken
        stats = {
            'total_purchases': len(purchased_items),
            'pending_purchases': len(pending_purchases),
            'total_spent': sum(item['purchase_amount'] for item in purchased_items),
            'pending_amount': sum(item['purchase_amount'] for item in pending_purchases)
        }

        print(f"DEBUG: Gefunden - {len(purchased_items)} bestätigte, {len(pending_purchases)} wartende Käufe")

        return render_template('my_purchases.html',
                               purchases=all_purchases,
                               stats=stats)

    except Exception as e:
        print(f"ERROR in my_purchases: {str(e)}")
        flash(f'Fehler beim Laden der Käufe: {str(e)}', 'danger')
        return redirect(url_for('marketplace'))


def find_original_item(item_id):
    """Findet Original-Upload mit verbessertem Logging"""

    print(f"DEBUG Original: Suche Original-Item für ID {item_id}")

    for block_idx, block in enumerate(blockchain.chain):
        for tx_idx, tx in enumerate(block.transactions):
            if (tx.get('type') in ['data_upload', 'model_upload']
                    and tx.get('transaction_id') == item_id):
                print(f"DEBUG Original: GEFUNDEN in Block {block_idx}, TX {tx_idx}")

                metadata = tx.get('metadata', {})
                return {
                    'name': metadata.get('name', 'Unknown'),
                    'description': metadata.get('description', ''),
                    'metadata': metadata,
                    'owner': tx.get('owner', 'Unknown'),
                    'price': tx.get('price', 0)
                }

    print(f"DEBUG Original: NICHT GEFUNDEN für ID {item_id}")
    return None



# Download Route für Marketplace-Items
@app.route('/marketplace/download/<item_id>')
@login_required
def download_item(item_id):
    """Download für gekaufte Items mit erweiterten Debug-Ausgaben"""

    try:
        user_address = session.get('blockchain_address')

        print(f"\n=== DEBUG DOWNLOAD START ===")
        print(f"User {user_address} möchte Item {item_id} downloaden")

        # 1. Prüfe Berechtigung
        has_permission = check_download_permission(user_address, item_id)
        print(f"Berechtigung für {item_id}: {has_permission}")

        if not has_permission:
            flash('Du hast keine Berechtigung zum Download dieses Items.', 'danger')
            return redirect(url_for('my_purchases'))

        # 2. Suche Original-Item
        original_item = find_original_item(item_id)
        if not original_item:
            print(f"Original Item {item_id} nicht gefunden")
            flash('Item nicht gefunden.', 'danger')
            return redirect(url_for('my_purchases'))

        print(f"Original Item gefunden: {original_item.get('name')}")

        # 3. Debug: Zeige alle verfügbaren Schlüssel BEVOR wir laden
        print(f"\n=== VERFÜGBARE SCHLÜSSEL VOR LADEN ===")
        show_available_keys()

        # 4. Lade Verschlüsselungsschlüssel mit Debug-Output
        print(f"\n=== SCHLÜSSEL-SUCHE ===")
        print(f"Suche Schlüssel für item_id: {item_id}, user: {user_address}")

        encryption_key = load_encryption_key(item_id, user_address)
        if not encryption_key:
            print(f"FEHLER: Kein Schlüssel für Item {item_id} und User {user_address} gefunden")

            # Versuche auch ohne User-Spezifikation (für Owner)
            print(f"Versuche Owner-Schlüssel zu finden...")
            encryption_key = load_encryption_key(item_id, None)

            if not encryption_key:
                print(f"FEHLER: Auch kein Owner-Schlüssel gefunden")
                flash('Verschlüsselungsschlüssel nicht gefunden.', 'danger')
                return redirect(url_for('my_purchases'))

        print(f"Schlüssel gefunden! Länge: {len(encryption_key) if encryption_key else 0}")

        # 5. Debug der Datenbank-Zugriffsprüfung
        print(f"\n=== DATENBANK-ZUGRIFF DEBUG ===")
        debug_database_access(user_address, item_id)

        # 6. Lade und entschlüssele Datei
        try:
            print(f"Versuche Datei zu entschlüsseln...")
            decrypted_content = blockchain.get_data_file(user_address, item_id, encryption_key)
            print(f"Entschlüsselung erfolgreich, {len(decrypted_content)} Bytes")

            # 7. Bereite Download vor
            metadata = original_item['metadata']
            filename = metadata.get('original_filename', f"{metadata.get('name', 'download')}.dat")

            file_stream = io.BytesIO(decrypted_content)
            file_stream.seek(0)

            content_type = get_content_type(filename)

            print(f"Sende Datei {filename} ({content_type})")
            print(f"=== DEBUG DOWNLOAD ENDE ===\n")

            return send_file(
                file_stream,
                as_attachment=True,
                download_name=filename,
                mimetype=content_type
            )

        except Exception as decrypt_error:
            print(f"ENTSCHLÜSSELUNGSFEHLER: {str(decrypt_error)}")
            flash(f'Fehler beim Entschlüsseln der Datei: {str(decrypt_error)}', 'danger')
            return redirect(url_for('my_purchases'))

    except Exception as e:
        print(f"ALLGEMEINER FEHLER in download_item: {str(e)}")
        flash(f'Download-Fehler: {str(e)}', 'danger')
        return redirect(url_for('my_purchases'))


def debug_database_access(user_address, item_id):
    """Debug-Funktion für Datenbank-Zugriff"""

    print(f"=== DATENBANK DEBUG ===")

    session_db = blockchain.db_manager.get_session()
    try:
        # Prüfe User in Datenbank
        from database import User, DataEntry
        user = session_db.query(User).filter_by(address=user_address).first()
        print(f"User in DB gefunden: {user is not None}")
        if user:
            print(f"User ID: {user.id}")

        # Prüfe DataEntry
        data_entry = session_db.query(DataEntry).filter_by(data_id=item_id).first()
        print(f"DataEntry gefunden: {data_entry is not None}")
        if data_entry:
            print(f"DataEntry ID: {data_entry.id}, Owner ID: {data_entry.owner_id}")
            print(f"Purchased_by count: {len(data_entry.purchased_by)}")

            if user:
                is_in_purchased_by = user in data_entry.purchased_by
                print(f"User ist in purchased_by: {is_in_purchased_by}")

                # Zeige alle Käufer
                for buyer in data_entry.purchased_by:
                    print(f"  Käufer: {buyer.address}")

    except Exception as e:
        print(f"Datenbank-Debug Fehler: {e}")
    finally:
        session_db.close()

    print(f"=== DATENBANK DEBUG ENDE ===\n")

def check_download_permission(user_address, item_id):
    """Prüft Download-Berechtigung mit ausführlichem Debug-Output"""

    print(f"\n=== BERECHTIGUNGS-PRÜFUNG ===")
    print(f"User: {user_address}, Item: {item_id}")

    # 1. Prüfe ob User der Owner ist
    original_item = find_original_item(item_id)
    if original_item and original_item.get('owner') == user_address:
        print(f"✓ User ist OWNER von {item_id}")
        return True

    print(f"✗ User ist NICHT Owner")

    # 2. Prüfe ob User das Item gekauft hat
    print(f"Prüfe Käufe in der Blockchain...")

    purchase_found = False
    for block_idx, block in enumerate(blockchain.chain):
        for tx_idx, tx in enumerate(block.transactions):
            if (tx.get('type') in ['data_purchase', 'model_purchase']
                    and tx.get('buyer') == user_address):

                purchased_item_id = tx.get('data_id') or tx.get('model_id')

                print(
                    f"  Block {block_idx}, TX {tx_idx}: {tx.get('type')} von {tx.get('buyer')} -> Item {purchased_item_id}")

                if purchased_item_id == item_id:
                    print(f"✓ PURCHASE MATCH gefunden!")
                    purchase_found = True
                    break

        if purchase_found:
            break

    if not purchase_found:
        print(f"✗ KEIN Kauf von {item_id} durch {user_address} gefunden")

    print(f"=== BERECHTIGUNG: {'JA' if purchase_found else 'NEIN'} ===\n")
    return purchase_found


def load_encryption_key(item_id, user_address=None):
    """Verbesserte Schlüssel-Lade-Funktion mit ausführlichem Debug-Output"""

    print(f"load_encryption_key_debug: item_id={item_id}, user={user_address}")

    # Alle möglichen Schlüssel-Dateien durchsuchen
    key_files = ['data_keys.json', 'EncryptionKeys.json']

    for key_file in key_files:
        print(f"Prüfe Datei: {key_file}")

        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    keys_data = json.load(f)

                datasets = keys_data.get('datasets', [])
                print(f"  -> {len(datasets)} Einträge in {key_file}")

                # Debug: Zeige alle Einträge
                for i, dataset in enumerate(datasets):
                    stored_id = dataset.get('data_id')
                    purchased_by = dataset.get('purchased_by')
                    name = dataset.get('name', 'Unknown')
                    print(f"    Eintrag {i}: data_id={stored_id}, purchased_by={purchased_by}, name={name}")

                # Suche nach passendem Eintrag
                print(f"  -> Suche nach Matches...")

                # 1. Zuerst nach Käufer-spezifischem Eintrag suchen
                if user_address:
                    print(f"    Suche Käufer-Eintrag für user {user_address}...")
                    for i, dataset in enumerate(datasets):
                        stored_id = dataset.get('data_id')
                        purchased_by = dataset.get('purchased_by')

                        if stored_id == item_id and purchased_by == user_address:
                            encryption_key = dataset.get('encryption_key')
                            print(
                                f"    KÄUFER-MATCH! Eintrag {i}, Schlüssel: {encryption_key[:20]}..." if encryption_key else "None")
                            return encryption_key

                # 2. Dann nach Owner-Eintrag suchen (ohne purchased_by)
                print(f"    Suche Owner-Eintrag...")
                for i, dataset in enumerate(datasets):
                    stored_id = dataset.get('data_id')
                    purchased_by = dataset.get('purchased_by')

                    if stored_id == item_id and not purchased_by:
                        encryption_key = dataset.get('encryption_key')
                        print(
                            f"    OWNER-MATCH! Eintrag {i}, Schlüssel: {encryption_key[:20]}..." if encryption_key else "None")
                        return encryption_key

                print(f"  -> Keine Matches in {key_file}")

            except Exception as e:
                print(f"  -> FEHLER beim Lesen von {key_file}: {e}")
        else:
            print(f"  -> {key_file} existiert nicht")

    print(f"KEIN Schlüssel für {item_id} und User {user_address} gefunden!")
    return None


def show_available_keys():
    """Debug-Funktion: Zeigt alle verfügbaren Schlüssel detailliert"""

    print("=== ALLE VERFÜGBAREN SCHLÜSSEL ===")

    key_files = ['data_keys.json', 'EncryptionKeys.json']

    for key_file in key_files:
        print(f"\nDatei: {key_file}")

        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    keys_data = json.load(f)

                datasets = keys_data.get('datasets', [])
                print(f"  Anzahl Einträge: {len(datasets)}")

                for i, dataset in enumerate(datasets):
                    data_id = dataset.get('data_id', 'NO_ID')
                    name = dataset.get('name', 'NO_NAME')
                    purchased_by = dataset.get('purchased_by', 'NONE')
                    has_key = 'YES' if dataset.get('encryption_key') else 'NO'

                    print(f"  [{i}] ID: {data_id}")
                    print(f"      Name: {name}")
                    print(f"      Purchased_by: {purchased_by}")
                    print(f"      Has_key: {has_key}")
                    print(f"      ---")

            except Exception as e:
                print(f"  FEHLER beim Lesen: {e}")
        else:
            print(f"  EXISTIERT NICHT")

    print("=== ENDE SCHLÜSSEL-LISTE ===\n")

def get_content_type(filename):
    """Bestimmt Content-Type basierend auf Dateiendung"""

    extension = filename.lower().split('.')[-1] if '.' in filename else ''

    content_types = {
        'csv': 'text/csv',
        'json': 'application/json',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'zip': 'application/zip',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pkl': 'application/octet-stream',
        'h5': 'application/octet-stream',
        'onnx': 'application/octet-stream',
        'pt': 'application/octet-stream',
        'pth': 'application/octet-stream'
    }

    return content_types.get(extension, 'application/octet-stream')


# API Route für Status-Updates (AJAX)
@app.route('/api/purchases/status')
@login_required
def purchase_status_api():
    """API für Live-Updates des Purchase-Status"""

    try:
        user_address = session.get('blockchain_address')

        # Zähle pending vs confirmed purchases
        pending_count = 0
        confirmed_count = 0

        # Pending transactions
        for tx in blockchain.current_transactions:
            if (tx.get('type') in ['data_purchase', 'model_purchase']
                    and tx.get('buyer') == user_address):
                pending_count += 1

        # Confirmed transactions
        for block in blockchain.chain:
            for tx in block.transactions:
                if (tx.get('type') in ['data_purchase', 'model_purchase']
                        and tx.get('buyer') == user_address):
                    confirmed_count += 1

        return jsonify({
            'pending_purchases': pending_count,
            'confirmed_purchases': confirmed_count,
            'total_purchases': pending_count + confirmed_count,
            'last_update': time.time()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    ### starte entweder manuell app.py (sonst wird automatisch flask ausgefuehrt) oder starte app.py --reset um datenbank und ipfs simulation zu resetten
    print("=== APP START ===")
    print("Führe Database Reset durch...")

    result = reset_database()
    if result:
        print("✅ Reset erfolgreich")
    else:
        print("❌ Reset fehlgeschlagen")

    print("Starte Flask App...")
    app.run(debug=True)