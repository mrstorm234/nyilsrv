from flask import Flask, request, jsonify, render_template
from datetime import datetime
import socket
import json
import os
import threading

app = Flask(__name__)

DATA_FILE = "clients.json"
CONFIG_FILE = "config.json"
LOCK = threading.Lock()
OFFLINE_THRESHOLD = 15  # detik

# =====================
# HELPER JSON
# =====================
def load_clients():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_clients(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"interval_seconds": 1500, "enabled": True}  # default 25 menit ON
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"interval_seconds": 1500, "enabled": True}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def now_ts():
    return int(datetime.utcnow().timestamp())

# =====================
# PING (CLIENT -> SERVER)
# =====================
@app.route("/ping", methods=["GET", "POST"])
def ping():
    if request.method == "POST":
        data = request.json or {}
        hostname = data.get("hostname", "unknown")
        ip = request.remote_addr

        with LOCK:
            clients = load_clients()
            clients[hostname] = {
                "hostname": hostname,
                "ip": ip,
                "last_seen": now_ts()
            }
            save_clients(clients)

        return jsonify({
            "ok": 1,
            "server": "nyilsrv-server"
        })

    return jsonify({
        "ok": 1,
        "server": socket.gethostname()
    })

# =====================
# SET INTERVAL
# =====================
@app.route("/set_interval", methods=["POST"])
def set_interval():
    seconds = int(request.form.get("seconds", 1500))
    enabled = request.form.get("enabled") == "on"
    cfg = load_config()
    cfg["interval_seconds"] = seconds
    cfg["enabled"] = enabled
    save_config(cfg)
    return "Interval updated. <a href='/'>Kembali</a>"

# =====================
# INDEX (HTML)
# =====================
@app.route("/")
def index():
    with LOCK:
        clients_data = load_clients()
    cfg = load_config()

    now = now_ts()
    clients = []

    for idx, (hostname, c) in enumerate(sorted(clients_data.items()), start=1):
        last_seen = c.get("last_seen", 0)
        delta = now - last_seen if last_seen else 999999

        state = "ONLINE" if delta <= OFFLINE_THRESHOLD else "OFFLINE"
        last_seen_ago = delta if last_seen else "tidak pernah"

        clients.append({
            "id": idx,
            "hostname": hostname,
            "ip": c.get("ip", "-"),
            "state": state,
            "last_seen_ago": last_seen_ago
        })

    return render_template("index.html", clients=clients, cfg=cfg)

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
