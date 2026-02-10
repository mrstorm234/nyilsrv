from flask import Flask, request, render_template, redirect, jsonify
import json, time, os, socket

app = Flask(__name__)

BASE = os.path.dirname(__file__)
CLIENT_DB = os.path.join(BASE, "clients.json")
CFG_DB = os.path.join(BASE, "config.json")

SERVER_INFO = {
    "role": "nyilsrv-server",
    "hostname": socket.gethostname()
}

# ------------------ utils ------------------

def load_json(path, default):
    if not os.path.exists(path):
        json.dump(default, open(path, "w"), indent=2)
        return default
    return json.load(open(path))

def save_json(path, data):
    json.dump(data, open(path, "w"), indent=2)

def load_clients():
    return load_json(CLIENT_DB, [])

def save_clients(d):
    save_json(CLIENT_DB, d)

def load_cfg():
    return load_json(CFG_DB, {"interval_seconds": 10})

def save_cfg(d):
    save_json(CFG_DB, d)

# ------------------ routes ------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        clients=load_clients(),
        cfg=load_cfg()
    )

# 🔎 endpoint WAJIB untuk client scan
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "ok": 1,
        "server": SERVER_INFO["role"],
        "hostname": SERVER_INFO["hostname"]
    })

@app.route("/set_interval", methods=["POST"])
def set_interval():
    seconds = int(request.form["seconds"])
    cfg = load_cfg()
    cfg["interval_seconds"] = seconds
    save_cfg(cfg)
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    clients = load_clients()

    found = False
    for c in clients:
        if c["hostname"] == data["hostname"]:
            c["ip"] = data["ip"]
            c["state"] = "ONLINE"
            c["last_seen"] = time.time()
            found = True
            break

    if not found:
        clients.append({
            "id": len(clients) + 1,
            "hostname": data["hostname"],
            "ip": data["ip"],
            "state": "ONLINE",
            "last_seen": time.time()
        })

    save_clients(clients)
    return {"ok": 1}

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    clients = load_clients()

    for c in clients:
        if c["hostname"] == data["hostname"]:
            c["last_seen"] = time.time()
            c["state"] = "ONLINE"

    save_clients(clients)
    return {"ok": 1}

# ------------------ main ------------------

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
