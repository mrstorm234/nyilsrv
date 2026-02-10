from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json, os, threading, time

app = Flask(__name__)

DATA_FILE = "clients.json"
CONFIG_FILE = "config.json"
LOCK = threading.Lock()
OFFLINE_THRESHOLD = 60  # detik, client dianggap OFFLINE jika ping telat

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
        return {"interval_seconds": 1500, "enabled": True, "sudo_user":"user", "sudo_pass":"1"}
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"interval_seconds": 1500, "enabled": True, "sudo_user":"user", "sudo_pass":"1"}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def now_ts():
    return int(datetime.utcnow().timestamp())

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
            clients.append({"hostname": hostname, "ip": ip, "last_seen": now_ts(), "status":"OFF"})
        save_clients(clients)

    print(f"[HEARTBEAT/REGISTER] {hostname} - {ip}")
    return jsonify({"ok": 1, "msg": "heartbeat/registered"})

# =====================
# CLIENT STATUS API
# =====================
@app.route("/status/<hostname>")
def client_status(hostname):
    with LOCK:
        clients = load_clients()
        for c in clients:
            if c.get("hostname") == hostname:
                return jsonify({"status": c.get("status", "OFF")})
    return jsonify({"status": "OFF"})

# =====================
# SET INTERVAL + ON/OFF CONFIG
# =====================
@app.route("/set_interval", methods=["POST"])
def set_interval():
    seconds = int(request.form.get("seconds", 1500))
    enabled = request.form.get("enabled") == "on"
    sudo_user = request.form.get("sudo_user", "user")
    sudo_pass = request.form.get("sudo_pass", "1")

    cfg = load_config()
    cfg["interval_seconds"] = seconds
    cfg["enabled"] = enabled
    cfg["sudo_user"] = sudo_user
    cfg["sudo_pass"] = sudo_pass
    save_config(cfg)
    return "Interval updated. <a href='/'>Kembali</a>"

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
        last_seen_ago = delta if last_seen else "tidak pernah"

        clients.append({
            "id": idx,
            "hostname": c.get("hostname", "unknown"),
            "ip": c.get("ip", "-"),
            "status": c.get("status","OFF"),
            "state": state,
            "last_seen_ago": last_seen_ago
        })

    return render_template("index.html", clients=clients, cfg=cfg)

# =====================
# AUTO ROUND-ROBIN ON/OFF
# =====================
def auto_rotate_clients():
    while True:
        with LOCK:
