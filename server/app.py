from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json, os, threading, time

app = Flask(__name__)

DATA_FILE = "clients.json"
CONFIG_FILE = "config.json"
LOCK = threading.Lock()
OFFLINE_THRESHOLD = 60  # detik, heartbeat max delay

# =====================
# Helper JSON
# =====================
def load_clients():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def save_clients(clients):
    with open(DATA_FILE, "w") as f:
        json.dump(clients, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        cfg = {"interval_seconds": 300, "enabled": True}
        save_config(cfg)
        return cfg
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"interval_seconds": 300, "enabled": True}

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
            clients.append({
                "hostname": hostname,
                "ip": ip,
                "last_seen": now_ts(),
                "status": "OFF"  # default OFF
            })
        save_clients(clients)

    return jsonify({"ok": 1, "msg": "heartbeat/registered"})

# =====================
# SET INTERVAL + ENABLED
# =====================
@app.route("/set_interval", methods=["POST"])
def set_interval():
    seconds = int(request.form.get("seconds", 300))
    enabled = request.form.get("enabled") == "on"
    cfg = load_config()
    cfg["interval_seconds"] = seconds
    cfg["enabled"] = enabled
    save_config(cfg)
    return "Interval updated. <a href='/'>Kembali</a>"

# =====================
# GET CLIENT STATUS
# =====================
@app.route("/status/<hostname>")
def client_status(hostname):
    clients = load_clients()
    for c in clients:
        if c["hostname"] == hostname:
            return jsonify({"status": c.get("status","OFF")})
    return jsonify({"status":"OFF"})

# =====================
# MANUAL SET CLIENT ON/OFF
# =====================
@app.route("/control/<hostname>/<action>")
def control(hostname, action):
    with LOCK:
        clients = load_clients()
        for c in clients:
            if c["hostname"] == hostname:
                if action.lower() == "on":
                    # matikan client lain
                    for other in clients:
                        if other["hostname"] != hostname:
                            other["status"] = "OFF"
                    c["status"] = "ON"
                else:
                    c["status"] = "OFF"
        save_clients(clients)
    return jsonify({"ok":1})

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
        clients.append({
            "id": idx,
            "hostname": c.get("hostname","unknown"),
            "ip": c.get("ip","-"),
            "status": c.get("status","OFF"),
            "state": state,
            "last_seen_ago": delta
        })
    return render_template("index.html", clients=clients, cfg=cfg)

# =====================
# ROTATE THREAD
# =====================
def rotate_clients():
    while True:
        try:
            cfg = load_config()
            if not cfg.get("enabled", True):
                time.sleep(5)
                continue
            with LOCK:
                clients = load_clients()
                now = time.time()
                online_clients = [c for c in clients if now - c.get("last_seen",0) <= OFFLINE_THRESHOLD]
                if online_clients:
                    # OFF semua dulu
                    for c in online_clients:
                        c["status"] = "OFF"
                    # pilih client pertama jadi ON
                    active = online_clients.pop(0)
                    active["status"] = "ON"
                    # update urutannya supaya bergantian
                    online_clients.append(active)
                    save_clients(clients)
            time.sleep(cfg.get("interval_seconds",300))
        except Exception as e:
            print("[ROTATE ERROR]", e)
            time.sleep(5)

threading.Thread(target=rotate_clients, daemon=True).start()

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
