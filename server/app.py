from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json, os, threading

app = Flask(__name__)

DATA_FILE = "clients.json"
CONFIG_FILE = "config.json"
LOCK = threading.Lock()
OFFLINE_THRESHOLD = 60  # detik

# =======================
# Helper JSON
# =======================
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
        return {
            "interval_seconds": 1500,
            "enabled": True,
            "rules": {},      # hostname -> ON/OFF
            "last_switch": 0,
            "sudo_user": "user",
            "sudo_pass": "1"
        }
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {
                "interval_seconds": 1500,
                "enabled": True,
                "rules": {},
                "last_switch": 0,
                "sudo_user": "user",
                "sudo_pass": "1"
            }

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def now_ts():
    return int(datetime.utcnow().timestamp())

# =======================
# Ping
# =======================
@app.route("/ping")
def ping():
    return jsonify({"server": "nyilsrv-server"})

# =======================
# Register / Heartbeat
# =======================
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

    return jsonify({"ok": 1, "msg": "heartbeat/registered"})

# =======================
# Set Interval & Sudo Credentials
# =======================
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
    cfg["last_switch"] = now_ts()

    # aturan awal: 1 client ON (index 0), sisanya OFF
    clients = load_clients()
    rules = {}
    for idx, c in enumerate(clients):
        rules[c["hostname"]] = "ON" if idx == 0 else "OFF"
    cfg["rules"] = rules

    save_config(cfg)
    return "Interval & rules updated. <a href='/'>Kembali</a>"

# =======================
# Switch Rules ON/OFF
# =======================
def switch_rules_if_needed():
    cfg = load_config()
    if not cfg.get("enabled", True):
        return

    now = now_ts()
    interval = cfg.get("interval_seconds", 1500)
    last = cfg.get("last_switch", 0)

    if now - last >= interval:
        rules = cfg.get("rules", {})
        if rules:
            hostnames = list(rules.keys())
            # cari yang ON, set OFF, client selanjutnya ON
            try:
                current_on = hostnames.index(next(h for h in hostnames if rules[h] == "ON"))
            except StopIteration:
                current_on = -1
            # set semua OFF
            for h in rules:
                rules[h] = "OFF"
            # ON client selanjutnya
            next_on = (current_on + 1) % len(hostnames)
            rules[hostnames[next_on]] = "ON"
            cfg["rules"] = rules
            cfg["last_switch"] = now
            save_config(cfg)
            print(f"[SWITCH RULES] {hostnames[next_on]} ON, others OFF")

# =======================
# Client Status Endpoint
# =======================
@app.route("/client_status/<hostname>")
def client_status(hostname):
    switch_rules_if_needed()
    cfg = load_config()
    status = cfg.get("rules", {}).get(hostname, "OFF") if cfg.get("enabled", True) else "OFF"
    # sertakan credential sudo untuk client
    return jsonify({
        "status": status,
        "sudo_user": cfg.get("sudo_user"),
        "sudo_pass": cfg.get("sudo_pass")
    })

# =======================
# Index HTML
# =======================
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

# =======================
# Main
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
