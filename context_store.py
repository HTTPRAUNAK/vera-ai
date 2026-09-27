"""
context_store.py - In-memory versioned store for magicpin AI Challenge.
Guarantees idempotency and rejects stale versions with HTTP 409 Conflict.
"""
import copy
import hashlib
import json
from typing import Dict, Any, Tuple, Optional, List

class ContextStore:
    def __init__(self):
        self._contexts: Dict[str, Dict[str, Any]] = {}
        self._versions: Dict[str, int] = {}
        self._payload_hashes: Dict[str, str] = {}
        self._histories: Dict[str, List[Dict[str, str]]] = {}

    def _hash_payload(self, data: Dict[str, Any]) -> str:
        dumped = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()

    def save_context(self, payload: Dict[str, Any]) -> Tuple[bool, str, int]:
        merchant_id = payload.get("merchant_id") or payload.get("merchant", {}).get("merchant_id") or "default_merchant"
        incoming_version = int(payload.get("version", 1))
        current_version = self._versions.get(merchant_id, 0)
        current_hash = self._payload_hashes.get(merchant_id, "")
        incoming_hash = self._hash_payload(payload)

        if merchant_id in self._versions:
            if incoming_version < current_version:
                return False, f"Stale version: incoming {incoming_version} < current {current_version}", 409
            elif incoming_version == current_version:
                if incoming_hash == current_hash:
                    return True, "Idempotent update: version and payload unchanged", 200
                else:
                    return False, f"Conflict: version {incoming_version} already exists with different payload", 409

        self._contexts[merchant_id] = copy.deepcopy(payload)
        self._versions[merchant_id] = incoming_version
        self._payload_hashes[merchant_id] = incoming_hash
        return True, "Context saved successfully", 200

    def get_context(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        return self._contexts.get(merchant_id)

    def get_version(self, merchant_id: str) -> int:
        return self._versions.get(merchant_id, 0)

    def get_history(self, merchant_id: str) -> List[Dict[str, str]]:
        if merchant_id not in self._histories:
            self._histories[merchant_id] = []
        return self._histories[merchant_id]

    def add_history(self, merchant_id: str, role: str, text: str) -> None:
        if merchant_id not in self._histories:
            self._histories[merchant_id] = []
        self._histories[merchant_id].append({"role": role, "text": text})

    def clear(self):
        self._contexts.clear()
        self._versions.clear()
        self._payload_hashes.clear()
        self._histories.clear()

context_store = ContextStore()
