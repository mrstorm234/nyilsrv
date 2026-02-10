from flask import Flask, request, jsonify
from datetime import datetime
import socket
import json
import os
import threading

app = Flask(__name__)

DATA_FILE = "clients.json"
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
# LIST CLIENTS
# =====================
@app.route("/clients", methods=["GET"])
def list_clients():
    with LOCK:
        clients = load_clients()

    now = now_ts()
    result = []

    for idx, (hostname, c) in enumerate(sorted(clients.items()), start=1):
        last_seen = c.get("last_seen", 0)
        delta = now - last_seen if last_seen else 999999

        status = "ONLINE" if delta <= OFFLINE_THRESHOLD else "OFFLINE"

        last_seen_txt = (
            f"{delta} detik lalu" if last_seen else "tidak pernah"
        )

        result.append({
            "id": idx,
            "hostname": hostname,
            "ip": c.get("ip", "-"),
            "status": status,
            "last_seen": last_seen_txt
        })

    return jsonify(result)

# =====================
# ROOT
# =====================
@app.route("/")
def index():
    return jsonify({
        "service": "NYILSRV Server",
        "status": "RUNNING",
        "clients": len(load_clients())
    })

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
