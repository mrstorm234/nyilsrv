from flask import Flask, request, render_template, redirect
import json, time, os

app = Flask(__name__)

BASE = os.path.dirname(__file__)
CLIENT_DB = os.path.join(BASE, "clients.json")
CFG_DB = os.path.join(BASE, "config.json")

def load_clients():
    return json.load(open(CLIENT_DB))

def save_clients(d):
    json.dump(d, open(CLIENT_DB, "w"), indent=2)

def load_cfg():
    return json.load(open(CFG_DB))

def save_cfg(d):
    json.dump(d, open(CFG_DB, "w"), indent=2)

@app.route("/")
def index():
    return render_template(
        "index.html",
        clients=load_clients(),
        cfg=load_cfg()
    )

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

    if not any(c["hostname"] == data["hostname"] for c in clients):
        clients.append({
            "id": len(clients) + 1,
            "hostname": data["hostname"],
            "ip": data["ip"],
            "state": "WAITING",
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

    save_clients(clients)
    return {"ok": 1}

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
