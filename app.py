from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from marketplace import MarketplaceBlockchain
from database import DatabaseManager, User, DataEntry, ModelEntry, EncryptedFile
from encryption import decrypt_file
from key_manager import save_key, get_key
import json
import base64
import datetime
from datetime import time
import sqlite3
import csv
import io
import os
import sys
import functools
# Import the model training class
from model_training import ModelTrainer
# Import der Datenbankinitialisierungsfunktionen
from database_handling import handle_database_initialization
# Ueberpruefung, ob die ipfs simulation existiert
os.makedirs("Storage_IPFS_sim/ipfs_data/objects", exist_ok=True)
os.makedirs("Storage_IPFS_sim/ipfs_data/temp", exist_ok=True)
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        # Get form data
        user_address = request.form.get('user_address')

        if not user_address:
            flash('User address is required', 'danger')
            return render_template('login.html')

        # Check if user exists in the database
        db_manager = blockchain.db_manager
        db_session = db_manager.get_session()

        try:
            user = db_session.query(User).filter_by(address=user_address).first()

            # If user doesn't exist, create one
            if not user:
                user = User(address=user_address)
                db_session.add(user)
                db_session.commit()
                flash('New user created with address: ' + user_address, 'success')

            # Set session variables
            session['user_address'] = user_address
            flash('Login successful!', 'success')

            # Redirect to the intended page or dashboard
            next_page = request.args.get('next', 'index')
            return redirect(url_for(next_page))

        except Exception as e:
            flash(f'Error during login: {str(e)}', 'danger')
            return render_template('login.html')
        finally:
            db_session.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_address', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

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
                        if encrypted_file:
                            try:
                                # Get the owner (user)
                                owner = session_db.query(User).filter_by(id=data_entry.owner_id).first()

                                # Determine where to get the content from (IPFS or database)
                                encrypted_content = None
                                if encrypted_file.ipfs_cid:
                                    # Get from IPFS
                                    encrypted_content = blockchain.ipfs.get(encrypted_file.ipfs_cid)
                                elif encrypted_file.encrypted_content:
                                    # Get from database
                                    encrypted_content = encrypted_file.encrypted_content

                                if encrypted_content:
                                    # Decrypt the content
                                    key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                                    decrypted_content = decrypt_file(encrypted_content, key)

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
                                        'has_more': has_more,
                                        'storage': 'IPFS' if encrypted_file.ipfs_cid else 'Database'
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


@app.route('/admin/test-data-access/<data_id>')
@admin_required
def admin_test_data_access(data_id):
    try:
        # Get key info from the saved keys
        key_data = get_key(data_id)
        if not key_data:
            return "No encryption key found for this data ID"

        # Get the decrypted content
        content = blockchain.get_data_file(
            "user1_address",  # Use a test user address
            data_id,
            key_data["encryption_key"]
        )

        # For text/CSV content
        try:
            text_content = content.decode('utf-8')
            return f"<h3>Successfully retrieved and decrypted {len(text_content)} characters of data</h3><pre>{text_content[:1000]}</pre>"
        except:
            return f"Successfully retrieved binary data of size {len(content)} bytes"

    except Exception as e:
        return f"Error accessing data: {str(e)}"
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


# Initialize the model trainer with IPFS
model_trainer = ModelTrainer(blockchain.ipfs)


@app.route('/training/available-datasets', methods=['GET'])
def get_available_datasets():
    """Get datasets available for training"""
    if 'user_address' not in session:
        return jsonify({"error": "Authentication required"}), 401

    user_address = session.get('user_address')

    db_manager = blockchain.db_manager
    db_session = db_manager.get_session()

    try:
        # Get user object
        user = db_session.query(User).filter_by(address=user_address).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get datasets owned or purchased by user
        owned_datasets = db_session.query(DataEntry).filter_by(owner_id=user.id).all()
        purchased_datasets = user.purchased_data

        # Combine and convert to JSON
        all_datasets = []

        for dataset in (list(owned_datasets) + list(purchased_datasets)):
            metadata = json.loads(dataset.data_metadata) if dataset.data_metadata else {}

            all_datasets.append({
                "data_id": dataset.data_id,
                "name": metadata.get("name", "Unnamed Dataset"),
                "description": metadata.get("description", ""),
                "owner": dataset.owner.address if dataset.owner else "Unknown",
                "owned": dataset.owner_id == user.id
            })

        return jsonify({"datasets": all_datasets})
    finally:
        db_session.close()


@app.route('/training/train-model', methods=['POST'])
def train_model():
    """Train a model on a dataset"""
    if 'user_address' not in session:
        return jsonify({"error": "Authentication required"}), 401

    user_address = session.get('user_address')

    # Get request data
    data = request.json
    dataset_id = data.get('dataset_id')
    algorithm_type = data.get('algorithm_type')
    target_column = data.get('target_column')
    model_name = data.get('model_name', 'Unnamed Model')
    model_description = data.get('model_description', '')

    if not all([dataset_id, algorithm_type, target_column]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Check access to dataset
    try:
        # Get dataset content
        dataset_content = blockchain.get_data_file(user_address, dataset_id, data.get('encryption_key', ''))

        if not dataset_content:
            return jsonify({"error": "Could not retrieve dataset"}), 404

        # Train the model
        result = model_trainer.train_model(
            dataset_content,
            algorithm_type,
            target_column,
            data.get('algorithm_params', {})
        )

        if "error" in result:
            return jsonify(result), 400

        # Create model metadata
        model_metadata = {
            "name": model_name,
            "description": model_description,
            "algorithm_type": algorithm_type,
            "target_column": target_column,
            "dataset_id": dataset_id,
            "training_metrics": result['metrics'],
            "training_time": result['training_time'],
            "features_count": result['features_count'],
            "samples_count": result['samples_count'],
            "creation_date": time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # Register the model in the blockchain
        model_id, tx_id = blockchain.register_trained_model(
            user_address,
            dataset_id,
            result['model_cid'],
            model_metadata
        )

        # Return success with model information
        return jsonify({
            "success": True,
            "model_id": model_id,
            "transaction_id": tx_id,
            "metrics": result['metrics'],
            "training_time": result['training_time']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/training/models', methods=['GET'])
def get_user_models():
    """Get models owned by the current user"""
    if 'user_address' not in session:
        return jsonify({"error": "Authentication required"}), 401

    user_address = session.get('user_address')

    db_manager = blockchain.db_manager
    db_session = db_manager.get_session()

    try:
        # Get user object
        user = db_session.query(User).filter_by(address=user_address).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get models owned by user
        models = db_session.query(ModelEntry).filter_by(owner_id=user.id).all()

        # Convert to JSON
        model_list = []

        for model in models:
            metadata = json.loads(model.model_metadata) if model.model_metadata else {}

            model_list.append({
                "model_id": model.model_id,
                "name": metadata.get("name", "Unnamed Model"),
                "description": metadata.get("description", ""),
                "algorithm_type": metadata.get("algorithm_type", "Unknown"),
                "target_column": metadata.get("target_column", ""),
                "dataset_id": metadata.get("dataset_id", ""),
                "metrics": metadata.get("training_metrics", {}),
                "creation_date": metadata.get("creation_date", "")
            })

        return jsonify({"models": model_list})
    finally:
        db_session.close()


@app.route('/training/model/<model_id>', methods=['GET'])
def get_model_details(model_id):
    """Get detailed information about a model"""
    if 'user_address' not in session:
        return jsonify({"error": "Authentication required"}), 401

    user_address = session.get('user_address')

    db_manager = blockchain.db_manager
    db_session = db_manager.get_session()

    try:
        # Get model entry
        model_entry = db_session.query(ModelEntry).filter_by(model_id=model_id).first()

        if not model_entry:
            return jsonify({"error": "Model not found"}), 404

        # Check if user has access
        user = db_session.query(User).filter_by(address=user_address).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if model_entry.owner_id != user.id and user not in model_entry.purchased_by:
            return jsonify({"error": "Access denied"}), 403

        # Get model metadata
        metadata = json.loads(model_entry.model_metadata) if model_entry.model_metadata else {}

        # Get blockchain transactions related to this model
        training_tx = None

        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.get("type") == "model_training" and tx.get("model_cid") == metadata.get("ipfs_cid"):
                    training_tx = tx
                    break
            if training_tx:
                break

        # Combine information
        model_details = {
            "model_id": model_entry.model_id,
            "name": metadata.get("name", "Unnamed Model"),
            "description": metadata.get("description", ""),
            "algorithm_type": metadata.get("algorithm_type", "Unknown"),
            "target_column": metadata.get("target_column", ""),
            "dataset_id": metadata.get("dataset_id", ""),
            "metrics": metadata.get("training_metrics", {}),
            "features_count": metadata.get("features_count", 0),
            "samples_count": metadata.get("samples_count", 0),
            "creation_date": metadata.get("creation_date", ""),
            "owner": model_entry.owner.address if model_entry.owner else "Unknown",
            "training_transaction": training_tx["transaction_id"] if training_tx else None,
            "ipfs_cid": metadata.get("ipfs_cid", "")
        }

        return jsonify(model_details)
    finally:
        db_session.close()


@app.route('/training/dashboard')
def training_dashboard():
    """View the training dashboard"""
    if 'user_address' not in session:
        # Redirect to login with 'next' parameter to return to dashboard after login
        return redirect(url_for('login', next='training_dashboard'))

    # User is authenticated, render the training dashboard
    return render_template('training_dashboard.html')


@app.route('/training/model/<model_id>/view')
def view_model_details(model_id):
    """View detailed model information"""
    if 'user_address' not in session:
        return redirect(url_for('index'))

    user_address = session.get('user_address')

    db_manager = blockchain.db_manager
    db_session = db_manager.get_session()

    try:
        # Get model details
        model_details = {}  # Get this from the API endpoint
        response = requests.get(f'{request.url_root}training/model/{model_id}',
                                headers={'Authorization': f'Bearer {session.get("token")}'})

        if response.status_code != 200:
            flash('Failed to load model details', 'danger')
            return redirect(url_for('training_dashboard'))

        model_data = response.json()

        # Get dataset details if needed
        dataset_data = {}
        if model_data.get('dataset_id'):
            dataset = db_session.query(DataEntry).filter_by(data_id=model_data['dataset_id']).first()
            if dataset:
                metadata = json.loads(dataset.data_metadata) if dataset.data_metadata else {}
                dataset_data = {
                    'data_id': dataset.data_id,
                    'name': metadata.get('name', 'Unnamed Dataset'),
                    'owner': dataset.owner.address if dataset.owner else 'Unknown'
                }

        # Get transaction timestamp
        training_timestamp = "Unknown"
        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.get('transaction_id') == model_data.get('training_transaction'):
                    training_timestamp = datetime.fromtimestamp(tx.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S')
                    break

        return render_template('model_details.html',
                               model=model_data,
                               dataset=dataset_data,
                               training_timestamp=training_timestamp)
    finally:
        db_session.close()
@app.route('/training/model-predict/<model_id>', methods=['POST'])
def predict_with_model(model_id):
    """Use a model to make predictions"""
    if 'user_address' not in session:
        return jsonify({"error": "Authentication required"}), 401

    user_address = session.get('user_address')

    # Get prediction data from request
    prediction_data = request.json.get('data')
    if not prediction_data:
        return jsonify({"error": "No prediction data provided"}), 400

    db_manager = blockchain.db_manager
    db_session = db_manager.get_session()

    try:
        # Get model entry
        model_entry = db_session.query(ModelEntry).filter_by(model_id=model_id).first()

        if not model_entry:
            return jsonify({"error": "Model not found"}), 404

        # Check if user has access
        user = db_session.query(User).filter_by(address=user_address).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if model_entry.owner_id != user.id and user not in model_entry.purchased_by:
            return jsonify({"error": "Access denied"}), 403

        # Get IPFS CID from metadata
        metadata = json.loads(model_entry.model_metadata) if model_entry.model_metadata else {}
        ipfs_cid = metadata.get("ipfs_cid")

        if not ipfs_cid:
            return jsonify({"error": "Model not available in IPFS"}), 404

        # Use the model to make predictions
        prediction_result = model_trainer.predict(ipfs_cid, prediction_data)

        if "error" in prediction_result:
            return jsonify(prediction_result), 400

        return jsonify({
            "model_id": model_id,
            "predictions": prediction_result["predictions"],
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)