from flask import Flask, request, jsonify, render_template, redirect
import time, threading

app = Flask(__name__)
LOCK = threading.Lock()

clients = {}
ACTIVE_UNIT = None


@app.route("/")
def index():
    return render_template("index.html", clients=clients, active=ACTIVE_UNIT, now=time.time())


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    uid = data["unit_id"]

    with LOCK:
        if uid not in clients:
            clients[uid] = {
                "hostname": data.get("hostname"),
                "ip": data.get("ip"),
                "status": "OFF",
                "last_seen": time.time()
            }
        else:
            clients[uid]["ip"] = data.get("ip")
            clients[uid]["last_seen"] = time.time()

    return jsonify(ok=True)


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    uid = request.json["unit_id"]
    with LOCK:
        if uid in clients:
            clients[uid]["last_seen"] = time.time()
    return jsonify(ok=True)


@app.route("/status/<uid>")
def status(uid):
    with LOCK:
        return jsonify(status=clients.get(uid, {}).get("status", "OFF"))


@app.route("/set/<uid>/<state>")
def set_state(uid, state):
    global ACTIVE_UNIT
    with LOCK:
        for k in clients:
            clients[k]["status"] = "OFF"

        if state == "ON":
            clients[uid]["status"] = "ON"
            ACTIVE_UNIT = uid
        else:
            ACTIVE_UNIT = None

    return redirect("/")


@app.route("/offline_check")
def offline_check():
    now = time.time()
    with LOCK:
        for uid in clients:
            if now - clients[uid]["last_seen"] > 15:
                clients[uid]["status"] = "OFF"
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
