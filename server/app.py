from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import json, os, threading

app = Flask(__name__)

DATA_FILE = "clients.json"
CONFIG_FILE = "config.json"
LOCK = threading.Lock()
OFFLINE_THRESHOLD = 60  # detik, supaya client bisa muncul ONLINE meski ping telat

# =====================
# Helper JSON
# =====================
def load_clients():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_clients(clients):
    with open(DATA_FILE, "w") as f:
        json.dump(clients, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        # default: interval 25 menit
        return {"interval_seconds": 1500, "enabled": True, "rules": {}}
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"interval_seconds": 1500, "enabled": True, "rules": {}}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def now_ts():
    return int(datetime.utcnow().timestamp())

# =====================
# PING
# =====================
@app.route("/ping")
def ping():
    return jsonify({"server": "nyilsrv-server"})

# =====================
# REGISTER / HEARTBEAT
# =====================
@app.route("/register", methods=["POST"])
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json or {}
    hostname = data.get("hostname", "unknown")
    ip = data.get("ip", request.remote_addr)

    with LOCK:
        clients = load_clients()
        found = False
        for c in clients:
            if c.get("hostname") == hostname:
                c["ip"] = ip
                c["last_seen"] = now_ts()
                found = True
                break
        if not found:
            clients.append({"hostname": hostname, "ip": ip, "last_seen": now_ts()})
        save_clients(clients)

    print(f"[HEARTBEAT/REGISTER] {hostname} - {ip}")
    return jsonify({"ok": 1, "msg": "heartbeat/registered"})

# =====================
# SET INTERVAL + RULES
# =====================
@app.route("/set_interval", methods=["POST"])
def set_interval():
    seconds = int(request.form.get("seconds", 1500))
    enabled = request.form.get("enabled") == "on"
    cfg = load_config()
    cfg["interval_seconds"] = seconds
    cfg["enabled"] = enabled

    # atur rules: ON/OFF bergantian tiap interval
    # misal client ganjil ON, genap OFF
    clients = load_clients()
    rules = {}
    for idx, c in enumerate(clients):
        # Alternating ON/OFF
        rules[c["hostname"]] = "ON" if idx % 2 == 0 else "OFF"
    cfg["rules"] = rules

    save_config(cfg)
    return "Interval & rules updated. <a href='/'>Kembali</a>"

# =====================
# GET CLIENT STATUS
# =====================
@app.route("/client_status/<hostname>")
def client_status(hostname):
    cfg = load_config()
    # default OFF
    status = cfg.get("rules", {}).get(hostname, "OFF") if cfg.get("enabled", True) else "OFF"
    return jsonify({"status": status})

# =====================
# INDEX HTML
# =====================
@app.route("/")
def index():
    with LOCK:
        clients_data = load_clients()
    cfg = load_config()

    now = now_ts()
    clients = []

    for idx, c in enumerate(clients_data, start=1):
        last_seen = c.get("last_seen", 0)
        delta = now - last_seen if last_seen else 999999
        state = "ONLINE" if delta <= OFFLINE_THRESHOLD else "OFFLINE"
        last_seen_ago = f"{delta} detik yang lalu" if last_seen else "tidak pernah"

        # ambil status ON/OFF dari rules
        status = cfg.get("rules", {}).get(c.get("hostname"), "OFF") if cfg.get("enabled", True) else "OFF"

        clients.append({
            "id": idx,
            "hostname": c.get("hostname", "unknown"),
            "ip": c.get("ip", "-"),
            "state": state,
            "last_seen_ago": last_seen_ago,
            "status": status
        })

    return render_template("index.html", clients=clients, cfg=cfg)

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
