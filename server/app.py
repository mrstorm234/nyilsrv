from flask import Flask, request, render_template, redirect, jsonify
import json, time, os, socket, threading

app = Flask(__name__)

BASE = os.path.dirname(__file__)
CLIENT_DB = os.path.join(BASE, "clients.json")
CFG_DB = os.path.join(BASE, "config.json")

SERVER_INFO = {
    "role": "nyilsrv-server",
    "hostname": socket.gethostname()
}

OFFLINE_AFTER = 30
LOCK = threading.Lock()

# ---------------- utils ----------------

def safe_load_json(path, default):
    with LOCK:
        try:
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump(default, f, indent=2)
                return default
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print("[JSON LOAD ERROR]", e)
            return default

def safe_save_json(path, data):
    with LOCK:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)

def load_clients():
    return safe_load_json(CLIENT_DB, [])

def save_clients(d):
    safe_save_json(CLIENT_DB, d)

def load_cfg():
    return safe_load_json(CFG_DB, {"interval_seconds": 10})

def save_cfg(d):
    safe_save_json(CFG_DB, d)

# --------------- routes ----------------

@app.route("/")
def index():
    now = time.time()
    clients = load_clients()

    for c in clients:
        last_seen = c.get("last_seen", 0)
        delta = int(now - last_seen)

        c["last_seen_ago"] = delta
        c["state"] = "OFFLINE" if delta > OFFLINE_AFTER else "ONLINE"

    save_clients(clients)

    return render_template(
        "index.html",
        clients=clients,
        cfg=load_cfg()
    )

@app.route("/ping")
def ping():
    return jsonify({
        "ok": 1,
        "server": SERVER_INFO["role"],
        "hostname": SERVER_INFO["hostname"]
    })

@app.route("/set_interval", methods=["POST"])
def set_interval():
    cfg = load_cfg()
    cfg["interval_seconds"] = int(request.form["seconds"])
    save_cfg(cfg)
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    hostname = data.get("hostname")
    ip = data.get("ip")

    if not hostname or not ip:
        return {"ok": 0}, 400

    clients = load_clients()

    for c in clients:
        if c["hostname"] == hostname:
            c.update({
                "ip": ip,
                "last_seen": time.time(),
                "state": "ONLINE"
            })
            save_clients(clients)
            return {"ok": 1}

    clients.append({
        "id": len(clients) + 1,
        "hostname": hostname,
        "ip": ip,
        "last_seen": time.time(),
        "state": "ONLINE"
    })

    save_clients(clients)
    return {"ok": 1}

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json or {}
    hostname = data.get("hostname")
    ip = request.remote_addr

    if not hostname:
        return {"ok": 0}, 400

    clients = load_clients()

    for c in clients:
        if c["hostname"] == hostname:
            c.update({
                "ip": ip,
                "last_seen": time.time(),
                "state": "ONLINE"
            })
            save_clients(clients)
            return {"ok": 1}

    # auto register fallback
    clients.append({
        "id": len(clients) + 1,
        "hostname": hostname,
        "ip": ip,
        "last_seen": time.time(),
        "state": "ONLINE"
    })

    save_clients(clients)
    return {"ok": 1}

# 🧯 global error handler
@app.errorhandler(Exception)
def handle_error(e):
    print("[SERVER ERROR]", e)
    return "Internal Server Error", 500

# --------------- main ----------------

if __name__ == "__main__":
    app.run("0.0.0.0", 5000, threaded=True)
