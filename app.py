from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from marketplace import MarketplaceBlockchain
from database import DatabaseManager, User, DataEntry, ModelEntry, EncryptedFile
from encryption import decrypt_file
from key_manager import save_key, get_key
import json
import base64
import datetime
import sqlite3
import csv
import io
import os
import sys
import functools

# Import der Datenbankinitialisierungsfunktionen
from database_handling import handle_database_initialization

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Blockchain-Instanz erstellen
blockchain = MarketplaceBlockchain()

# Datenbank initialisieren je nach Bedarf
# --reset als Kommandozeilenparameter verwenden, um die Datenbank zurückzusetzen
reset_mode = '--reset' in sys.argv
handle_database_initialization(blockchain, reset_db=reset_mode)

# Admin configuration
ADMIN_PASSWORD = "passwort"  # Simple password as requested

# Rest deines Codes bleibt unverändert...
# Custom Jinja2 filter for timestamp formatting
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Decorator for routes that require admin authentication
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Home page
@app.route('/')
def index():
    return render_template('index.html')


# Dataset upload page
@app.route('/upload-dataset')
def upload_dataset_page():
    return render_template('upload_dataset.html')


# Blockchain viewer
@app.route('/view-blockchain')
def view_blockchain():
    # Get the blockchain data
    blockchain_data = []
    for block in blockchain.chain:
        blockchain_data.append(block.to_dict())
    return render_template('blockchain_view.html', blockchain_data=blockchain_data)


# Admin login page
@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')


@app.route('/admin/reset-system', methods=['POST'])
@admin_required
def admin_reset_system():
    try:
        # 1. Bestehende Verbindungen schließen
        db_manager = blockchain.db_manager
        session_db = db_manager.get_session()

        # 2. Datenbank leeren statt löschen
        try:
            # SQLAlchemy Text-Objekt importieren
            from sqlalchemy import text

            # Alle Tabellen leeren mit text() Funktion
            session_db.execute(text("DELETE FROM encrypted_files"))
            session_db.execute(text("DELETE FROM data_purchases"))
            session_db.execute(text("DELETE FROM model_purchases"))
            session_db.execute(text("DELETE FROM data_entries"))
            session_db.execute(text("DELETE FROM model_entries"))
            session_db.execute(text("DELETE FROM users"))
            session_db.commit()

            # 3. Schlüsseldatei zurücksetzen
            import json
            import os
            if os.path.exists('data_keys.json'):
                with open('data_keys.json', 'w') as f:
                    json.dump({"datasets": []}, f)

            # 4. Blockchain zurücksetzen
            # Blockchain-Instanz neu initialisieren
            blockchain.__init__()  # Initialisiert die Blockchain neu

            flash("System wurde erfolgreich zurückgesetzt", "success")
        except Exception as db_error:
            session_db.rollback()
            flash(f"Fehler beim Zurücksetzen der Datenbank: {str(db_error)}", "danger")
        finally:
            session_db.close()

    except Exception as e:
        flash(f"Fehler beim Zurücksetzen: {str(e)}", "danger")

    return redirect(url_for('admin_dashboard'))

# Admin login processing
@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    password = request.form.get('password')

    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin_login.html', error="Invalid password. Please try again.")


# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))


# Admin dashboard
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


# Database viewer page
@app.route('/admin/database')
@admin_required
def admin_database():
    # Connect to the database
    db_manager = blockchain.db_manager
    session_db = db_manager.get_session()

    try:
        # Get users
        users = session_db.query(User).all()

        # Get data entries
        data_entries = session_db.query(DataEntry).all()

        # Get model entries
        model_entries = session_db.query(ModelEntry).all()

        # Get encrypted files (with sample of encrypted content)
        encrypted_files_query = session_db.query(EncryptedFile).all()
        encrypted_files = []

        for file in encrypted_files_query:
            # Create a sample of the encrypted content
            encrypted_sample = str(file.encrypted_content[:100]) + "..." if file.encrypted_content else "No content"

            encrypted_file = {
                'id': file.id,
                'file_hash': file.file_hash,
                'encryption_key_hash': file.encryption_key_hash,
                'data_entry_id': file.data_entry_id,
                'model_entry_id': file.model_entry_id,
                'encrypted_content_sample': encrypted_sample
            }
            encrypted_files.append(encrypted_file)

        # Prepare decrypted data from keys in data_keys.json
        decrypted_data = []
        if os.path.exists('data_keys.json'):
            with open('data_keys.json', 'r') as f:
                keys_data = json.load(f)

                for dataset in keys_data.get('datasets', []):
                    data_id = dataset.get('data_id')
                    encryption_key = dataset.get('encryption_key')
                    name = dataset.get('name', 'Unknown')

                    # Find the corresponding data entry
                    data_entry = session_db.query(DataEntry).filter_by(data_id=data_id).first()
                    if data_entry:
                        # Find the encrypted file
                        encrypted_file = session_db.query(EncryptedFile).filter_by(data_entry_id=data_entry.id).first()
                        if encrypted_file and encrypted_file.encrypted_content:
                            try:
                                # Get the owner (user)
                                owner = session_db.query(User).filter_by(id=data_entry.owner_id).first()

                                # Decrypt the content
                                key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                                decrypted_content = decrypt_file(encrypted_file.encrypted_content, key)

                                # Detect file type and prepare preview
                                is_csv = name.lower().endswith('.csv')
                                content_preview = ""
                                has_more = False

                                if is_csv:
                                    # Parse CSV data
                                    csv_content = decrypted_content.decode('utf-8')
                                    csv_reader = csv.reader(io.StringIO(csv_content))
                                    rows = []
                                    for i, row in enumerate(csv_reader):
                                        if i < 10:  # Show only first 10 rows
                                            rows.append(row)
                                        else:
                                            has_more = True
                                            break
                                    content_preview = rows
                                else:
                                    # Text preview for other files
                                    try:
                                        text_content = decrypted_content.decode('utf-8')
                                        if len(text_content) > 1000:
                                            content_preview = text_content[:1000] + "..."
                                            has_more = True
                                        else:
                                            content_preview = text_content
                                    except UnicodeDecodeError:
                                        content_preview = "Binary content (cannot display preview)"

                                # Add to the decrypted data list
                                decrypted_data.append({
                                    'data_id': data_id,
                                    'name': name,
                                    'owner': owner.address if owner else 'Unknown',
                                    'file_type': 'CSV' if is_csv else 'Text/Binary',
                                    'content_preview': content_preview,
                                    'is_csv': is_csv,
                                    'has_more': has_more
                                })
                            except Exception as e:
                                print(f"Error decrypting {data_id}: {str(e)}")

        return render_template('database_view.html',
                               users=users,
                               data_entries=data_entries,
                               model_entries=model_entries,
                               encrypted_files=encrypted_files,
                               decrypted_data=decrypted_data)
    finally:
        session_db.close()


# Blockchain status page
@app.route('/admin/blockchain')
@admin_required
def admin_blockchain():
    # For now, just redirect to view-blockchain
    return redirect(url_for('view_blockchain'))


# Users management page
@app.route('/admin/users')
@admin_required
def admin_users():
    # Will be implemented later
    return "User Management - Coming Soon"


# Mining controls page
@app.route('/admin/mining')
@admin_required
def admin_mining():
    # Will be implemented later
    return "Mining Controls - Coming Soon"


@app.route('/api/upload-dataset', methods=['POST'])
def upload_dataset():
    owner_address = request.form.get('owner_address')
    name = request.form.get('name')
    description = request.form.get('description')
    price = float(request.form.get('price', 0))

    # Get the uploaded file
    if 'dataset_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['dataset_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Read the file content
    file_content = file.read()

    # Create metadata
    metadata = {
        'name': name,
        'description': description,
        'format': file.content_type,
        'filename': file.filename,
        'size': len(file_content)
    }

    try:
        # Register the user if not already registered
        blockchain.register_user(owner_address)

        # Upload the data to the blockchain and database
        data_id, encryption_key = blockchain.upload_data_with_file(
            owner_address, file_content, metadata, price
        )

        # Mine a block to include the transaction
        blockchain.mine_block(difficulty=2)  # Lower difficulty for demonstration

        # Save the key for later access
        save_key(file.filename, data_id, encryption_key)

        return render_template('upload_success.html',
                               data_id=data_id,
                               encryption_key=encryption_key)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['POST'])
def register_user():
    data = request.json
    address = data.get('address')
    public_key = data.get('public_key')

    if not address:
        return jsonify({'error': 'Address is required'}), 400

    try:
        user = blockchain.register_user(address, public_key)
        return jsonify({'message': 'User registered', 'address': address}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data', methods=['POST'])
def upload_data():
    data = request.json
    owner_address = data.get('owner_address')
    file_content = data.get('file_content')  # Base64-encoded file content
    metadata = data.get('metadata', {})
    price = data.get('price', 0)

    if not all([owner_address, file_content]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Base64-decodieren
        decoded_content = base64.b64decode(file_content)

        data_id, encryption_key = blockchain.upload_data_with_file(
            owner_address, decoded_content, metadata, price)

        # Save the key for later access
        filename = metadata.get('filename', 'unknown_file')
        save_key(filename, data_id, encryption_key)

        return jsonify({
            'data_id': data_id,
            'encryption_key': encryption_key,
            'message': 'Data uploaded successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/models', methods=['POST'])
def upload_model():
    data = request.json
    owner_address = data.get('owner_address')
    file_content = data.get('file_content')  # Base64-encoded file content
    metadata = data.get('metadata', {})
    price = data.get('price', 0)

    if not all([owner_address, file_content]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Base64-decodieren
        decoded_content = base64.b64decode(file_content)

        model_id, encryption_key = blockchain.upload_model_with_file(
            owner_address, decoded_content, metadata, price)

        # Save the key for later access
        filename = metadata.get('filename', 'unknown_model')
        save_key(filename, model_id, encryption_key)

        return jsonify({
            'model_id': model_id,
            'encryption_key': encryption_key,
            'message': 'Model uploaded successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/<data_id>/purchase', methods=['POST'])
def purchase_data(data_id):
    data = request.json
    buyer_address = data.get('buyer_address')
    amount = data.get('amount', 0)

    if not buyer_address:
        return jsonify({'error': 'Buyer address is required'}), 400

    try:
        encryption_key = blockchain.purchase_data(buyer_address, data_id, amount)
        return jsonify({
            'message': 'Data purchased successfully',
            'encryption_key': encryption_key
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/<data_id>/content', methods=['POST'])
def get_data_content(data_id):
    data = request.json
    user_address = data.get('user_address')
    encryption_key = data.get('encryption_key')

    if not all([user_address, encryption_key]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        content = blockchain.get_data_file(user_address, data_id, encryption_key)

        # Base64-encodieren für die Rückgabe
        encoded_content = base64.b64encode(content).decode()

        return jsonify({
            'content': encoded_content,
            'message': 'Data retrieved successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 403  # Forbidden


# Added download function for the admin page
@app.route('/admin/download/<data_id>')
@admin_required
def admin_download_data(data_id):
    try:
        # Get key info from the saved keys
        key_data = get_key(data_id)
        if not key_data:
            flash("No encryption key found for this data ID", "danger")
            return redirect(url_for('admin_database'))

        # Get user from database
        db_manager = blockchain.db_manager
        session_db = db_manager.get_session()
        try:
            data_entry = session_db.query(DataEntry).filter_by(data_id=data_id).first()
            if not data_entry:
                flash("Data entry not found", "danger")
                return redirect(url_for('admin_database'))

            # Find the owner
            user = session_db.query(User).filter_by(id=data_entry.owner_id).first()
            user_address = user.address if user else "admin"

            # Get the decrypted content
            content = blockchain.get_data_file(
                user_address,
                data_id,
                key_data["encryption_key"]
            )

            # Create a response with the file
            from flask import send_file
            import io

            # Create an in-memory file-like object
            file_data = io.BytesIO(content)
            filename = key_data.get("name", f"data_{data_id}.csv")

            # Send the file to the client
            return send_file(
                file_data,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv' if filename.endswith('.csv') else 'application/octet-stream'
            )

        finally:
            session_db.close()

    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('admin_database'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)