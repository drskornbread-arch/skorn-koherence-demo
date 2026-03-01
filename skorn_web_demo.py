from flask import Flask, render_template_string, redirect, url_for
import hashlib
import json
import copy

app = Flask(__name__)

# -----------------------------
# Deterministic Utilities
# -----------------------------

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def state_hash(state):
    return hashlib.sha256(canonical_json(state).encode()).hexdigest()

def apply_delta(state, delta):
    new_state = copy.deepcopy(state)
    new_state["counter"] += delta.get("inc", 0)
    new_state["version"] += 1
    return new_state

# -----------------------------
# Global Demo State
# -----------------------------

engineA = {"counter": 0, "version": 0}
engineB = {"counter": 0, "version": 0}
status = "VERIFIED"
message = "Systems synchronized."
cycle = 0
event_log = []
# -----------------------------
# HTML Template
# -----------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
<title><title>SKORN Koherence — Deterministic Engine</title></title>
<style>
body { font-family: Arial; background:#111; color:#eee; text-align:center; }
.container { display:flex; justify-content:space-around; margin-top:40px; }
.panel { background:#222; padding:20px; width:40%; border-radius:10px; }
.status { margin-top:40px; font-size:24px; }
.green { color:#00ff88; }
.red { color:#ff4444; }
button { padding:10px 20px; margin:20px; font-size:16px; border:none; border-radius:6px; }
.run { background:#007bff; color:white; }
.drift { background:#ff4444; color:white; }
.reset {
    background:#222;
    color:#fff;
    border:1px solid #888;
}

.status-live {
    animation: glowGreen 1.5s ease-in-out infinite alternate;
}
@keyframes glowGreen {
    from { text-shadow: 0 0 5px #00ff88; }
    to   { text-shadow: 0 0 15px #00ff88; }
}

.status-halt {
    animation: pulseRed 1s infinite;
}
@keyframes pulseRed {
    0%   { opacity: 1; }
    50%  { opacity: 0.6; }
    100% { opacity: 1; }
}
</style>
</head>
<body>

<h1>SKORN Koherence — Deterministic Engine</h1>
<p style="opacity:0.7; margin-top:-10px;">
Deterministic state validation across parallel execution engines.
</p>

<div class="container">
  <div class="panel">
    <h2>Engine A</h2>
    <p>State: {{engineA}}</p>
    <p>Hash: {{hashA}}</p>
  </div>
  <div class="panel">
    <h2>Engine B</h2>
    <p>State: {{engineB}}</p>
    <p>Hash: {{hashB}}</p>
  </div>
</div>

</div>

<div class="status">
  {% if status == "VERIFIED" %}
    <div class="green status-live">✓ VERIFIED — Advancement Allowed</div>
  {% else %}
    <div class="red status-halt">✖ DIVERGENCE DETECTED — Advancement Halted</div>
  {% endif %}
  <p>{{message}}</p>
</div>

<div>
  <a href="/next"><button class="run">Run Next Cycle</button></a>
  <a href="/drift"><button class="drift">Inject Drift</button></a>
  <a href="/reset"><button class="reset">Reset System</button></a>
</div>
<div class="log">
  <h3>Replay Log</h3>
  <ul>
    {% for e in event_log %}
      <li>{{ e }}</li>
    {% endfor %}
  </ul>
</div>
</body>
</html>
"""

# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return render_template_string(
        HTML,
        engineA=engineA,
        engineB=engineB,
        hashA=state_hash(engineA),
        hashB=state_hash(engineB),
        status=status,
        message=message,
        event_log=event_log
    )

@app.route("/next")
def next_cycle():
    global engineA, engineB, status, message, cycle, event_log

    if status != "VERIFIED":
        return redirect(url_for("home"))

    delta = {"inc": 1}
    engineA = apply_delta(engineA, delta)
    engineB = apply_delta(engineB, delta)
    cycle += 1
    event_log.append(f"Cycle {cycle}: increment applied")
    if state_hash(engineA) == state_hash(engineB):
        status = "VERIFIED"
        message = f"Cycle {cycle} validated."
        event_log.append(f"Cycle {cycle}: VERIFIED")
    else:
        status = "HALTED"
        message = "Unauthorized state mutation detected."
        event_log.append(f"Cycle {cycle}: HALTED (divergence)")
    return redirect(url_for("home"))
@app.route("/drift")
def inject_drift():
    global engineA, engineB, status, message, event_log

    # mutate ONLY one engine to force divergence
    engineA["counter"] += 5
    engineA["version"] += 1

    status = "HALTED"
    message = "Manual drift injected."
    event_log.append("DRIFT injected into Engine A")

    return redirect(url_for("home"))

    
             
    

    



            

    

    

if __name__ == "__main__":
    app.run(debug=False)