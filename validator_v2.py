import json
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


# -----------------------------
# Deterministic utilities
# -----------------------------

def canonical_json(obj: Any) -> str:
    # Deterministic serialization (critical)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def state_hash(state: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(state))

def sign_hmac(secret: bytes, payload: Dict[str, Any]) -> str:
    msg = canonical_json(payload).encode("utf-8")
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()

def verify_hmac(secret: bytes, payload: Dict[str, Any], sig_hex: str) -> bool:
    expected = sign_hmac(secret, payload)
    return hmac.compare_digest(expected, sig_hex)


# -----------------------------
# Receipt model
# -----------------------------

@dataclass(frozen=True)
class Receipt:
    cycle: int
    prev_receipt_hash: str
    delta: Dict[str, Any]
    expected_state_hash: str
    timestamp: float
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "prev_receipt_hash": self.prev_receipt_hash,
            "delta": self.delta,
            "expected_state_hash": self.expected_state_hash,
            "timestamp": self.timestamp,
        }

    def receipt_hash(self) -> str:
        # Receipt hash is computed from the unsigned receipt body + signature (so it’s tamper-evident)
        body = self.to_dict().copy()
        body["signature"] = self.signature
        return sha256_hex(canonical_json(body))


# -----------------------------
# Deterministic state transition
# -----------------------------

def apply_delta(state: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic transition function.
    You can evolve this later, but keep it pure & deterministic.
    """
    new_state = dict(state)

    # Example fields
    inc = int(delta.get("inc", 0))
    new_state["counter"] = int(new_state.get("counter", 0)) + inc

    # Strict version increment
    new_state["version"]