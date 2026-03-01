import json
import hashlib
import hmac
import time

# ------------------------
# Deterministic Utilities
# ------------------------

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def state_hash(state):
    return hashlib.sha256(canonical_json(state).encode()).hexdigest()

def sign(secret, payload):
    return hmac.new(secret, canonical_json(payload).encode(), hashlib.sha256).hexdigest()

# ------------------------
# Engine
# ------------------------

class Engine:
    def __init__(self, name):
        self.name = name
        self.state = {"counter": 0, "version": 0}
        self.last_hash = state_hash(self.state)

    def apply(self, delta, drift=False):
        self.state["counter"] += delta["inc"]
        self.state["version"] += 1

        if drift:
            print(f"{self.name} injected drift +3")
            self.state["counter"] += 3

        self.last_hash = state_hash(self.state)
        return self.last_hash

    def reset(self):
        self.state = {"counter": 0, "version": 0}
        self.last_hash = state_hash(self.state)

# ------------------------
# Validator
# ------------------------

class Validator:
    def __init__(self):
        self.secret = b"super_secret"
        self.last_hash = state_hash({"counter": 0, "version": 0})
        self.receipts = []

    def validate(self, cycle, prev_hash, delta, hash_a, hash_b):
        if prev_hash != self.last_hash:
            return False, "Previous hash mismatch"

        if hash_a != hash_b:
            return False, "Engine hash mismatch"

        receipt_payload = {
            "cycle": cycle,
            "prev_hash": prev_hash,
            "delta": delta,
            "new_hash": hash_a,
            "timestamp": time.time()
        }

        signature = sign(self.secret, receipt_payload)
        self.last_hash = hash_a
        self.receipts.append((receipt_payload, signature))
        return True, receipt_payload

# ------------------------
# Simulation
# ------------------------

def run_simulation():
    engine_a = Engine("EngineA")
    engine_b = Engine("EngineB")
    validator = Validator()

    deltas = [{"inc": 1} for _ in range(6)]

    for cycle, delta in enumerate(deltas, start=1):
        print(f"\nCycle {cycle}")

        drift = (cycle == 3)  # Inject drift at cycle 3
        hash_a = engine_a.apply(delta)
        hash_b = engine_b.apply(delta, drift=drift)

        ok, result = validator.validate(
            cycle,
            validator.last_hash,
            delta,
            hash_a,
            hash_b
        )

        if not ok:
            print("VALIDATION FAILED:", result)
            print("Resyncing EngineB...")
            engine_b.reset()

            # Replay all accepted receipts
            for receipt, _ in validator.receipts:
                engine_b.apply(receipt["delta"])

            hash_b = engine_b.last_hash

            ok, result = validator.validate(
                cycle,
                validator.last_hash,
                delta,
                hash_a,
                hash_b
            )

        if ok:
            print("ACCEPTED:", result)
        else:
            print("HALT")

    print("\nFinal state hash:", validator.last_hash)

run_simulation()