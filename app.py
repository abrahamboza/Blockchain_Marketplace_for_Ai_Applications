from flask import Flask, request, jsonify
from marketplace import MarketplaceBlockchain
import json
import base64

app = Flask(__name__)
blockchain = MarketplaceBlockchain()


@app.route('/')
def hello_world():
    return 'Blockchain Marketplace for AI Applications'


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


if __name__ == '__main__':
    app.run(debug=True, port=5000)