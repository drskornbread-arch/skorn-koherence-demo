from flask import Flask, redirect, url_for, render_template_string
import json
import hashlib

app = Flask(__name__)

engineA = {"counter": 0, "version": 0}
engineB = {"counter": 0, "version": 0}
cycle = 0
status = "VERIFIED"
message = "Systems synchronized."
event_log = []

def state_hash(state: dict) -> str:
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>SKORN Koherence Demo</title>
  <style>
    body { font-family: Arial, sans-serif; background:#0b0b0b; color:#eaeaea; margin:0; padding:24px; }
    .wrap { max-width: 980px; margin: 0 auto; }
    .row { display:flex; gap:16px; flex-wrap:wrap; }
    .card { flex:1; min-width:320px; background:#151515; border:1px solid #2a2a2a; border-radius:14px; padding:18px; }
    h1 { margin:0 0 14px; letter-spacing:0.5px; }
    h2 { margin:0 0 10px; }
    .hash { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; font-size:12px; color:#c9c9c9; word-break:break-all; }
    .status { margin:18px 0 6px; font-size:22px; font-weight:700; }
    .ok { color:#33ff66; }
    .bad { color:#ff4d4d; }
    .msg { color:#cfcfcf; margin-bottom:16px; }
    .btns { display:flex; gap:12px; flex-wrap:wrap; margin: 16px 0 18px; }
    a.btn { display:inline-block; padding:12px 16px; border-radius:10px; text-decoration:none; font-weight:700; border:1px solid #333; }
    .blue { background:#2d6cff; color:#fff; }
    .red { background:#ff3b30; color:#fff; }
    .gray { background:#2a2a2a; color:#fff; }
    .log { background:#0f0f0f; border:1px solid #262626; border-radius:12px; padding:14px; }
    .logline { font-family: ui-monospace, monospace; font-size:12px; color:#bfbfbf; padding:4px 0; border-bottom:1px solid #1f1f1f; }
    .logline:last-child { border-bottom:none; }
  </style>
</head>
<body>
<div class="wrap">
  <h1>SKORN</h1>

  <div class="row">
    <div class="card">
      <h2>Engine A</h2>
      <div>State: {{a_state}}</div>
      <div style="margin-top:10px;">Hash:</div>
      <div class="hash">{{a_hash}}</div>
    </div>

    <div class="card">
      <h2>Engine B</h2>
      <div>State: {{b_state}}</div>
      <div style="margin-top:10px;">Hash:</div>
      <div class="hash">{{b_hash}}</div>
    </div>
  </div>

  <div class="status {{ 'ok' if status == 'VERIFIED' else 'bad' }}">
    {{ '✓ VERIFIED — Advancement Allowed' if status == 'VERIFIED' else '✗ HALTED — Divergence Detected' }}
  </div>
  <div class="msg">{{message}}</div>

  <div class="btns">
    <a class="btn blue" href="{{url_for('next_cycle')}}">Run Next Cycle</a>
    <a class="btn red" href="{{url_for('inject_drift')}}">Inject Drift</a>
    <a class="btn gray" href="{{url_for('reset_system')}}">Reset System</a>
  </div>

  <h2>Replay Log</h2>
  <div class="log">
    {% if logs|length == 0 %}
      <div class="logline">No events yet.</div>
    {% else %}
      {% for line in logs %}
        <div class="logline">{{line}}</div>
      {% endfor %}
    {% endif %}
  </div>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(
        TEMPLATE,
        a_state=engineA,
        b_state=engineB,
        a_hash=state_hash(engineA),
        b_hash=state_hash(engineB),
        status=status,
        message=message,
        logs=event_log[-30:],
    )

@app.route("/next")
def next_cycle():
    global engineA, engineB, cycle, status, message, event_log

    cycle += 1

    # Normal deterministic advancement
    engineA["counter"] += 1
    engineB["counter"] += 1

    # Verify both hashes match
    ha = state_hash(engineA)
    hb = state_hash(engineB)

    if ha == hb:
        status = "VERIFIED"
        message = "Systems synchronized."
        event_log.append(f"Cycle {cycle}: VERIFIED (advance ok)")
    else:
        status = "HALTED"
        message = "Unauthorized state mutation detected."
        event_log.append(f"Cycle {cycle}: HALTED (divergence)")

    return redirect(url_for("home"))

@app.route("/drift")
def inject_drift():
    global engineA, status, message, event_log

    # Mutate ONLY engineA to force divergence
    engineA["counter"] += 5
    engineA["version"] += 1

    status = "HALTED"
    message = "Manual drift injected."
    event_log.append("DRIFT injected into Engine A")

    return redirect(url_for("home"))

@app.route("/reset")
def reset_system():
    global engineA, engineB, cycle, status, message, event_log

    engineA = {"counter": 0, "version": 0}
    engineB = {"counter": 0, "version": 0}
    cycle = 0
    status = "VERIFIED"
    message = "System reset."
    event_log = []

    return redirect(url_for("home"))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)