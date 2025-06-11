# simulated_ipfs.py
import hashlib
import os
import json
import shutil
import base64
from typing import Dict, Any, Optional, Union, Tuple

###
# Simulated IPFS-like storage system
# Es fehlen reale Nutzer und Nodes in der kompletten Implementierung
# Simuliere das Hashen der Daten und das Speichern in einem lokalen Verzeichnis mithilfer der CID
###
class SimulatedIPFS:

    def __init__(self, storage_dir: str = "ipfs_storage"):

        self.storage_dir = storage_dir
        self.objects_dir = os.path.join(storage_dir, "objects")
        self.pins_file = os.path.join(storage_dir, "pins.json")
        self.metadata_file = os.path.join(storage_dir, "metadata.json")

        # Erstellen der Verzeichnisse, falls sie nicht existieren
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(os.path.join(storage_dir, "temp"), exist_ok=True)

        # Initialisieren der Dateien, falls sie nicht existieren
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)

        if not os.path.exists(self.pins_file):
            with open(self.pins_file, 'w') as f:
                json.dump([], f)

    def _calculate_hash(self, content: bytes) -> str:

        return hashlib.sha256(content).hexdigest()

    def add(self, content: bytes, metadata: Dict[str, Any] = None) -> str:

        # Berechnen des CIDs (Content Identifier)
        cid = self._calculate_hash(content)

        # Speichern des Inhalts, falls er noch nicht existiert
        content_path = os.path.join(self.objects_dir, cid)
        if not os.path.exists(content_path):
            with open(content_path, 'wb') as f:
                f.write(content)

        # Update metadata
        if metadata:
            self._update_metadata(cid, metadata)

        return cid

    def get(self, cid: str) -> Optional[bytes]:

        content_path = os.path.join(self.objects_dir, cid)
        if os.path.exists(content_path):
            with open(content_path, 'rb') as f:
                return f.read()
        return None

    def pin(self, cid: str) -> bool:

        if not os.path.exists(os.path.join(self.objects_dir, cid)):
            return False

        with open(self.pins_file, 'r') as f:
            pins = json.load(f)

        if cid not in pins:
            pins.append(cid)

            with open(self.pins_file, 'w') as f:
                json.dump(pins, f)

        return True

    def unpin(self, cid: str) -> bool:

        with open(self.pins_file, 'r') as f:
            pins = json.load(f)

        if cid in pins:
            pins.remove(cid)

            with open(self.pins_file, 'w') as f:
                json.dump(pins, f)
            return True

        return False

    def _update_metadata(self, cid: str, metadata: Dict[str, Any]) -> None:

        with open(self.metadata_file, 'r') as f:
            all_metadata = json.load(f)

        all_metadata[cid] = metadata

        with open(self.metadata_file, 'w') as f:
            json.dump(all_metadata, f)

    def get_metadata(self, cid: str) -> Optional[Dict[str, Any]]:

        with open(self.metadata_file, 'r') as f:
            all_metadata = json.load(f)

        return all_metadata.get(cid)

    def list_objects(self) -> Dict[str, Dict[str, Any]]:

        with open(self.metadata_file, 'r') as f:
            return json.load(f)

    def list_pins(self) -> list:

        with open(self.pins_file, 'r') as f:
            return json.load(f)

    def exists(self, cid: str) -> bool:

        return os.path.exists(os.path.join(self.objects_dir, cid))

    def cleanup(self) -> int:

        with open(self.pins_file, 'r') as f:
            pins = json.load(f)

        removed = 0
        for filename in os.listdir(self.objects_dir):
            if filename not in pins:
                os.remove(os.path.join(self.objects_dir, filename))
                removed += 1

        return removed