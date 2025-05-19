# simulated_ipfs.py
import hashlib
import os
import json
import shutil
import base64
from typing import Dict, Any, Optional, Union, Tuple


class SimulatedIPFS:
    """
    A simplified simulation of IPFS functionality for local demonstration purposes.

    This class implements content-addressed storage where files are stored and retrieved
    by their content hash (similar to IPFS CIDs).
    """

    def __init__(self, storage_dir: str = "ipfs_storage"):
        """
        Initialize the simulated IPFS system.

        Args:
            storage_dir: Directory where content will be stored
        """
        self.storage_dir = storage_dir
        self.objects_dir = os.path.join(storage_dir, "objects")
        self.pins_file = os.path.join(storage_dir, "pins.json")
        self.metadata_file = os.path.join(storage_dir, "metadata.json")

        # Create necessary directories
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(os.path.join(storage_dir, "temp"), exist_ok=True)

        # Initialize metadata and pins if they don't exist
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)

        if not os.path.exists(self.pins_file):
            with open(self.pins_file, 'w') as f:
                json.dump([], f)

    def _calculate_hash(self, content: bytes) -> str:
        """
        Calculate the SHA-256 hash of the content, similar to IPFS CID generation.

        Args:
            content: The binary content to hash

        Returns:
            A hex string representation of the hash
        """
        return hashlib.sha256(content).hexdigest()

    def add(self, content: bytes, metadata: Dict[str, Any] = None) -> str:
        """
        Add content to the storage and return its CID.

        Args:
            content: Binary content to store
            metadata: Optional metadata about the content

        Returns:
            The content identifier (CID) as a string
        """
        # Calculate the content hash (CID)
        cid = self._calculate_hash(content)

        # Store the content
        content_path = os.path.join(self.objects_dir, cid)
        if not os.path.exists(content_path):
            with open(content_path, 'wb') as f:
                f.write(content)

        # Update metadata
        if metadata:
            self._update_metadata(cid, metadata)

        return cid

    def get(self, cid: str) -> Optional[bytes]:
        """
        Retrieve content by its CID.

        Args:
            cid: The content identifier

        Returns:
            The binary content or None if not found
        """
        content_path = os.path.join(self.objects_dir, cid)
        if os.path.exists(content_path):
            with open(content_path, 'rb') as f:
                return f.read()
        return None

    def pin(self, cid: str) -> bool:
        """
        Mark content as pinned (should be kept permanently).

        Args:
            cid: The content identifier to pin

        Returns:
            True if pinned successfully, False otherwise
        """
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
        """
        Remove a pin from content.

        Args:
            cid: The content identifier to unpin

        Returns:
            True if unpinned successfully, False otherwise
        """
        with open(self.pins_file, 'r') as f:
            pins = json.load(f)

        if cid in pins:
            pins.remove(cid)

            with open(self.pins_file, 'w') as f:
                json.dump(pins, f)
            return True

        return False

    def _update_metadata(self, cid: str, metadata: Dict[str, Any]) -> None:
        """
        Update metadata for a CID.

        Args:
            cid: The content identifier
            metadata: The metadata to associate with the content
        """
        with open(self.metadata_file, 'r') as f:
            all_metadata = json.load(f)

        all_metadata[cid] = metadata

        with open(self.metadata_file, 'w') as f:
            json.dump(all_metadata, f)

    def get_metadata(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a CID.

        Args:
            cid: The content identifier

        Returns:
            The metadata dictionary or None if not found
        """
        with open(self.metadata_file, 'r') as f:
            all_metadata = json.load(f)

        return all_metadata.get(cid)

    def list_objects(self) -> Dict[str, Dict[str, Any]]:
        """
        List all objects in storage with their metadata.

        Returns:
            Dictionary of CIDs and their metadata
        """
        with open(self.metadata_file, 'r') as f:
            return json.load(f)

    def list_pins(self) -> list:
        """
        List all pinned CIDs.

        Returns:
            List of pinned CIDs
        """
        with open(self.pins_file, 'r') as f:
            return json.load(f)

    def exists(self, cid: str) -> bool:
        """
        Check if a CID exists in storage.

        Args:
            cid: The content identifier

        Returns:
            True if exists, False otherwise
        """
        return os.path.exists(os.path.join(self.objects_dir, cid))

    def cleanup(self) -> int:
        """
        Remove unpinned objects to save space.

        Returns:
            Number of objects removed
        """
        with open(self.pins_file, 'r') as f:
            pins = json.load(f)

        removed = 0
        for filename in os.listdir(self.objects_dir):
            if filename not in pins:
                os.remove(os.path.join(self.objects_dir, filename))
                removed += 1

        return removed