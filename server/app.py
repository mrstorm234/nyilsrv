from flask import Flask, request, jsonify, render_template, redirect
import threading, time, json, os

app = Flask(__name__)
LOCK = threading.Lock()

BASE_DIR = os.path.dirname(__file__)
CLIENT_DB = os.path.join(BASE_DIR, "clients.json")
CFG_DB = os.path.join(BASE_DIR, "config.json")

# ===== LOAD/STORE CLIENTS =====
def load_clients():
    if not os.path.exists(CLIENT_DB):
        return {}
    return json.load(open(CLIENT_DB))

def save_clients(clients):
    json.dump(clients, open(CLIENT_DB, "w"), indent=2)

# ===== LOAD/STORE CONFIG =====
def load_config():
    if not os.path.exists(CFG_DB):
        cfg = {"interval_seconds": 1500, "enabled": True}
        save_config(cfg)
        return cfg
    return json.load(open(CFG_DB))

def save_config(cfg):
    json.dump(cfg, open(CFG_DB, "w"), indent=2)

# ===== GLOBAL VAR =====
ACTIVE_UNIT = None
ROTATE_ENABLED = True
ROTATE_INTERVAL = 1500

# ===== REGISTER =====
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    uid = data["unit_id"]
    hostname = data.get("hostname")
    ip = data.get("ip")
    with LOCK:
        clients = load_clients()
        clients[uid] = clients.get(uid, {})
        clients[uid].update({
            "hostname": hostname,
            "ip": ip,
            "last_seen": time.time(),
            "status": clients.get(uid, {}).get("status", "OFF")
        })
        save_clients(clients)
    return jsonify(ok=True)

# ===== HEARTBEAT =====
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    uid = request.json.get("unit_id")
    with LOCK:
        clients = load_clients()
        if uid in clients:
            clients[uid]["last_seen"] = time.time()
            save_clients(clients)
    return jsonify(ok=True)

# ===== GET STATUS UNTUK CLIENT =====
@app.route("/status/<uid>")
def status(uid):
    with LOCK:
        clients = load_clients()
        return jsonify(status=clients.get(uid, {}).get("status", "OFF"))

# ===== SET STATUS MANUAL =====
@app.route("/set/<uid>/<state>")
def set_state(uid, state):
    global ACTIVE_UNIT
    with LOCK:
        clients = load_clients()
        for k in clients:
            clients[k]["status"] = "OFF"
        if state == "ON":
            clients[uid]["status"] = "ON"
            ACTIVE_UNIT = uid
        else:
            ACTIVE_UNIT = None
        save_clients(clients)
    return redirect("/")

# ===== SET INTERVAL =====
@app.route("/set_interval", methods=["POST"])
def set_interval():
    global ROTATE_INTERVAL, ROTATE_ENABLED
    seconds = int(request.form.get("seconds", 1500))
    enabled = request.form.get("enabled") == "on"
    ROTATE_INTERVAL = seconds
    ROTATE_ENABLED = enabled
    cfg = {"interval_seconds": ROTATE_INTERVAL, "enabled": ROTATE_ENABLED}
    save_config(cfg)
    return redirect("/")

# ===== DASHBOARD =====
@app.route("/")
def index():
    with LOCK:
        clients = load_clients()
        cfg = load_config()
        now = time.time()
        return render_template(
            "index.html",
            clients=clients,
            active=ACTIVE_UNIT,
            now=now,
            interval=cfg["interval_seconds"],
            rotate_enabled=cfg["enabled"]
        )

# ===== ROTATE LOGIC =====
def rotate_clients():
    global ACTIVE_UNIT
    last_rotate = time.time()
    while True:
        time.sleep(1)
        cfg = load_config()
        interval = cfg.get("interval_seconds", 1500)
        if not cfg.get("enabled", True):
            continue
        clients = load_clients()
        online = [c for c in clients if time.time() - c.get("last_seen", 0) < 90]
        if not online:
            continue
        # hitung next index
        uids = list(clients.keys())
        if ACTIVE_UNIT not in uids:
            next_idx = 0
        else:
            idx = uids.index(ACTIVE_UNIT)
            next_idx = (idx + 1) % len(uids)
        # set OFF semua
        for uid in uids:
            clients[uid]["status"] = "OFF"
        # set ACTIVE
        ACTIVE_UNIT = uids[next_idx]
        clients[ACTIVE_UNIT]["status"] = "ON"
        save_clients(clients)
        last_rotate = time.time()
        print(f"[ROTATE] Active unit: {clients[ACTIVE_UNIT]['hostname']}")
        time.sleep(interval)

threading.Thread(target=rotate_clients, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
