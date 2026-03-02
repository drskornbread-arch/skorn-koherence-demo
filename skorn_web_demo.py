from flask import Flask, render_template_string, jsonify, redirect, url_for
import json
import hashlib

app = Flask(__name__)


class KoherenceState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.engines = {
            "A": {"counter": 0, "version": 0},
            "B": {"counter": 0, "version": 0}
        }
        self.hashes = {
            "A": self._hash(self.engines["A"]),
            "B": self._hash(self.engines["B"])
        }
        self.expected_hashes = self.hashes.copy()
        self.log = []
        self.cycle = 0
        self.drift_injected = False
        self.divergence_detected = False

    def _hash(self, state):
        canonical = json.dumps(state, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def advance(self):
        if self.divergence_detected:
            return

        self.cycle += 1

        # Apply SAME deterministic update to both engines
        for k in ["A", "B"]:
            self.engines[k]["counter"] += 1
            self.engines[k]["version"] += 1
            self.hashes[k] = self._hash(self.engines[k])

        self.log.append(f"Cycle {self.cycle}: A incremented")
        self.log.append(f"Cycle {self.cycle}: B incremented")

        # Engines must match each other
        if self.hashes["A"] != self.hashes["B"]:
            self.divergence_detected = True
            self.log.append("Divergence detected — halted")

        self.expected_hashes = self.hashes.copy()

    def inject_drift(self):
        if not self.drift_injected:
            self.engines["A"]["counter"] += 5
            self.hashes["A"] = self._hash(self.engines["A"])
            self.log.append("DRIFT injected into Engine A")
            self.drift_injected = True


state = KoherenceState()


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SKORN Koherence — Deterministic Engine</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f8f9fa; }
        h1 { color: #333; }
        .engines { display: flex; gap: 30px; }
        .engine { padding: 20px; border: 1px solid #ccc; border-radius: 8px; background: white; width: 45%; }
        .log { margin-top: 30px; padding: 15px; background: #e9ecef; border-radius: 8px; max-height: 300px; overflow-y: auto; }
        button { padding: 12px 20px; font-size: 16px; margin: 10px 10px 0 0; cursor: pointer; }
        .run { background: #28a745; color: white; border: none; }
        .drift { background: #ffc107; color: black; border: none; }
        .reset { background: #dc3545; color: white; border: none; }
        .divergence { color: #dc3545; font-weight: bold; font-size: 1.3em; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>SKORN Koherence — Deterministic Engine</h1>
    <p>Deterministic state validation across parallel execution engines.</p>

    {% if divergence_detected %}
    <div class="divergence">
        ✖ DIVERGENCE DETECTED — Advancement Halted<br>
        Manual drift injected.
    </div>
    {% endif %}

    <div class="engines">
        <div class="engine">
            <h3>Engine A</h3>
            <pre>State: {{ engines.A }}</pre>
            <pre>Hash: {{ hashes.A }}</pre>
        </div>
        <div class="engine">
            <h3>Engine B</h3>
            <pre>State: {{ engines.B }}</pre>
            <pre>Hash: {{ hashes.B }}</pre>
        </div>
    </div>

    <div>
        <button class="run" onclick="location.href='/next'">Run Next Cycle</button>
        <button class="drift" onclick="location.href='/inject'">Inject Drift</button>
        <button class="reset" onclick="location.href='/reset'">Reset System</button>
    </div>
       {% if drift_injected and not divergence_detected %}
<p style="margin-top:10px; font-size:14px; color:#555;">
Drift mutates state. Divergence is enforced on the next deterministic cycle (gate execution).
</p>
{% endif %}
    <div class="log">
        <h3>Replay Log</h3>
        <ul>
            {% for entry in log %}
            <li>{{ entry }}</li>
            {% endfor %}
        </ul>
    </div>

</body>
</html>
"""


@app.route('/')
def home():
    return render_template_string(
        HTML,
        engines=state.engines,
        hashes=state.hashes,
        log=state.log,
        divergence_detected=state.divergence_detected,
        drift_injected=state.drift_injected,
    )


@app.route('/next')
def next_cycle():
    state.advance()
    return redirect(url_for('home'))


@app.route('/inject')
def inject():
    state.inject_drift()
    return redirect(url_for('home'))


@app.route('/reset')
def reset():
    state.reset()
    return redirect(url_for('home'))


@app.route('/state')
def debug_state():
    return jsonify({
        "engines": state.engines,
        "hashes": state.hashes,
        "cycle": state.cycle,
        "log": state.log,
        "divergence": state.divergence_detected
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
