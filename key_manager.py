import json
import os
from flask import Flask, jsonify, request
from marketplace import MarketplaceBlockchain
import base64


# speichert einen Schlüssel für ein Datenset
def save_key(name, data_id, encryption_key):
    file_path = "data_keys.json"
    data = {
        "datasets": []
    }


    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:

            data = {"datasets": []}


    entry = {
        "name": name,
        "data_id": data_id,
        "encryption_key": encryption_key,
        "upload_date": "2025-05-04"  # Current date
    }


    for i, dataset in enumerate(data["datasets"]):
        if dataset["data_id"] == data_id:
            # Update existing entry
            data["datasets"][i] = entry
            break
    else:

        data["datasets"].append(entry)


    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Saved key for {name} with ID {data_id}")
    return True


# Holt den Schlüssel für ein Datenset basierend auf der ID
def get_key(data_id, user_address=None):
    """
    Holt einen Schlüssel - entweder als Owner oder als Käufer

    Args:
        data_id: Die ID der Daten
        user_address: Adresse des Users (optional)

    Returns:
        dict: Schlüssel-Informationen oder None
    """
    file_path = "data_keys.json"
    if not os.path.exists(file_path):
        print("No keys file found")
        return None

    with open(file_path, 'r') as f:
        data = json.load(f)

    for dataset in data["datasets"]:
        if dataset["data_id"] == data_id:
            # Prüfe ob der User der Owner ist (kein "purchased_by" Feld)
            if not dataset.get("purchased_by"):
                return dataset

            # Prüfe ob der User der Käufer ist
            if user_address and dataset.get("purchased_by") == user_address:
                return dataset

    print(f"No key found for data_id {data_id} and user {user_address}")
    return None

def get_key_for_user(data_id, user_address):
    """
    Spezielle Funktion um Schlüssel für einen bestimmten User zu finden
    (Owner oder Käufer)
    """
    file_path = "data_keys.json"
    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Suche zuerst nach Käufer-Eintrag
    for dataset in data["datasets"]:
        if (dataset["data_id"] == data_id and
            dataset.get("purchased_by") == user_address):
            return dataset

    # Wenn nicht als Käufer gefunden, suche nach Owner-Eintrag
    for dataset in data["datasets"]:
        if (dataset["data_id"] == data_id and
            not dataset.get("purchased_by")):
            # Das ist der Owner-Eintrag, prüfe ob User der Owner ist
            # (Das müsste eigentlich über die Blockchain geprüft werden)
            return dataset

    return None

# Funktion zum Abrufen von Daten basierend auf der ID
def retrieve_data(data_id, user_address="test_user"):

    key_info = get_key(data_id)
    if not key_info:
        return None, "Key not found"

    try:

        blockchain = MarketplaceBlockchain()


        content = blockchain.get_data_file(
            user_address,
            data_id,
            key_info["encryption_key"]
        )

        return content, None
    except Exception as e:
        return None, str(e)


# Flask App zum Testen der Schlüsselverwaltung
if __name__ == "__main__":
    # Save the diabetes dataset key
    save_key(
        "diabetes.csv",
        "3d13e161f11f42dab712b43ba0f008c8",
        "KwPVvtVdu65gEag9oNVgZ8GC2KgBn_zeU4U1nvIZXwc="
    )

    # Retrieve the key info
    diabetes_key = get_key("3d13e161f11f42dab712b43ba0f008c8")
    print("Retrieved key info:", diabetes_key)