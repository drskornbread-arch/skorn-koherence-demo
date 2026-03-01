import json
import hashlib
from threading import Thread, Lock
import time

def deterministic_state_hash(state: dict) -> str:
    canonical = json.dumps(state, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

class DeterministicCore:
    def __init__(self):
        self.state = {"counter": 0, "version": 0}
        self.cycle_id = 0
        self.drift_injected = False
        self.halted = False
        self.log = []
        self.lock = Lock()

    def log_cycle(self, actor: str, action: str, expected_hash: str = None):
        entry = {
            "cycle_id": self.cycle_id,
            "actor": actor,
            "action": action,
            "state": self.state.copy(),
            "hash": deterministic_state_hash(self.state),
            "expected_hash": expected_hash,
            "timestamp": time.time()
        }
        self.log.append(entry)
        print(f"[LOG] {entry['cycle_id']} | {actor} | {action} | "
              f"state={entry['state']} | hash={entry['hash'][:8]}... "
              f"expected={str(expected_hash)[:8]+'...' if expected_hash else 'n/a'}")

    def advance(self, actor: str):
        with self.lock:
            if self.halted:
                return

            # snapshot pre-state
            pre = self.state.copy()

            # predicted (valid) next state rule: +1 counter, +1 version
            predicted = {"counter": pre["counter"] + 1, "version": pre["version"] + 1}
            predicted_hash = deterministic_state_hash(predicted)

            # apply actual update
            self.state["counter"] += 1
            self.state["version"] += 1

            actual_hash = deterministic_state_hash(self.state)
            gate = "PASS" if actual_hash == predicted_hash else "HALT"

            self.log_cycle(actor, f"advance gate={gate}", expected_hash=predicted_hash)

            if gate == "HALT":
                print(f"\n[DETECTED] State mismatch in cycle {self.cycle_id}")
                print(f"  Expected: {predicted_hash[:12]}...")
                print(f"  Actual:   {actual_hash[:12]}...")
                self.halted = True
                self.reconcile_and_resume()

            self.cycle_id += 1

    def inject_drift(self):
        with self.lock:
            if self.halted or self.drift_injected:
                return
            # inject invalid mutation
            self.state["counter"] += 3
            self.drift_injected = True
            self.log_cycle("DriftInjector", "injected +3 drift")
            self.cycle_id += 1

    def reconcile_and_resume(self):
        # deterministic reconciliation rule: remove the injected drift exactly
        # (in real world: authoritative replay/quorum/etc.)
        # Here, we assume we know the drift signature (+3).
        self.state["counter"] -= 3
        reconciled_hash = deterministic_state_hash(self.state)

        print(f"[RECONCILE] Removed drift (-3) → state={self.state}")
        print(f"            New hash = {reconciled_hash[:12]}...")

        self.halted = False
        self.log_cycle("Reconciler", "state reconciled & resumed")
        self.cycle_id += 1

    def run_simulation(self):
        print("Starting deterministic simulation...\n")

        def process1():
            for _ in range(5):
                self.advance("P1")
                time.sleep(0.05)

        def process2():
            for i in range(5):
                self.advance("P2")
                if i == 2:
                    self.inject_drift()
                time.sleep(0.07)

        t1 = Thread(target=process1, name="Process-1")
        t2 = Thread(target=process2, name="Process-2")

        t1.start(); t2.start()
        t1.join(); t2.join()

        print("\nSimulation finished.")
        print(f"Final state: {self.state}")
        print(f"Final hash:  {deterministic_state_hash(self.state)[:16]}...")
        print(f"Log entries: {len(self.log)}")

if __name__ == "__main__":
    core = DeterministicCore()
    core.run_simulation()