from flask import Flask, request, jsonify, render_template
import json, os, time, threading

app = Flask(__name__)

CLIENT_FILE = "clients.json"
CONFIG_FILE = "config.json"
LOCK = threading.Lock()

DEFAULT_CONFIG = {
    "enabled": True,
    "interval": 1500,   # 25 menit
    "active": ""
}

OFFLINE_TIMEOUT = 30  # detik

# ---------- utils ----------
def load(path, default):
    if not os.path.exists(path):
        return default
    try:
        return json.load(open(path))
    except:
        return default

def save(path, data):
    json.dump(data, open(path, "w"), indent=2)

def now():
    return int(time.time())

# ---------- routes ----------
@app.route("/")
def index():
    clients = load(CLIENT_FILE, [])
    cfg = load(CONFIG_FILE, DEFAULT_CONFIG)

    for c in clients:
        c["state"] = "ONLINE" if now() - c["last_seen"] <= OFFLINE_TIMEOUT else "OFFLINE"
        c["ago"] = now() - c["last_seen"]

    return render_template("index.html", clients=clients, cfg=cfg)

@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    hostname = data.get("hostname")
    ip = data.get("ip") or request.remote_addr

    if not hostname:
        return jsonify(ok=False)

    with LOCK:
        clients = load(CLIENT_FILE, [])
        for c in clients:
            if c["hostname"] == hostname:
                c["ip"] = ip
                c["last_seen"] = now()
                save(CLIENT_FILE, clients)
                return jsonify(ok=True)

        clients.append({
            "hostname": hostname,
            "ip": ip,
            "last_seen": now()
        })
        save(CLIENT_FILE, clients)

    print("[REGISTER]", hostname, ip)
    return jsonify(ok=True)

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json or {}
    hostname = data.get("hostname")
    if not hostname:
        return jsonify(ok=False)

    with LOCK:
        clients = load(CLIENT_FILE, [])
        for c in clients:
            if c["hostname"] == hostname:
                c["last_seen"] = now()
                save(CLIENT_FILE, clients)
                return jsonify(ok=True)

    return jsonify(ok=False)

@app.route("/status/<hostname>")
def status(hostname):
    cfg = load(CONFIG_FILE, DEFAULT_CONFIG)
    if cfg["active"] == hostname:
        return jsonify(status="ON")
    return jsonify(status="OFF")

@app.route("/set", methods=["POST"])
def set_cfg():
    cfg = load(CONFIG_FILE, DEFAULT_CONFIG)
    cfg["enabled"] = "enabled" in request.form
    cfg["interval"] = int(request.form.get("interval", 1500))
    save(CONFIG_FILE, cfg)
    return "OK <a href='/'>Back</a>"

# ---------- scheduler ----------
def rotate():
    while True:
        with LOCK:
            cfg = load(CONFIG_FILE, DEFAULT_CONFIG)
            if not cfg["enabled"]:
                time.sleep(5)
                continue

            clients = load(CLIENT_FILE, [])
            online = [c for c in clients if now() - c["last_seen"] <= OFFLINE_TIMEOUT]

            if not online:
                time.sleep(5)
                continue

            names = [c["hostname"] for c in online]
            if cfg["active"] not in names:
                cfg["active"] = names[0]
            else:
                i = names.index(cfg["active"])
                cfg["active"] = names[(i + 1) % len(names)]

            save(CONFIG_FILE, cfg)

        time.sleep(cfg["interval"])

# ---------- main ----------
if __name__ == "__main__":
    threading.Thread(target=rotate, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
