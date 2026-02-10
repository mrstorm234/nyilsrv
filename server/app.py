from flask import Flask, request, jsonify, render_template, redirect
import time, threading

app = Flask(__name__)
LOCK = threading.Lock()

clients = {}  # key = UNIT_ID
ACTIVE_UNIT = None

# default interval 25 menit
ROTATE_INTERVAL = 25 * 60  # detik
ROTATE_ENABLED = True


@app.route("/")
def index():
    with LOCK:
        return render_template(
            "index.html",
            clients=clients,
            active=ACTIVE_UNIT,
            now=time.time(),
            interval=ROTATE_INTERVAL,
            rotate_enabled=ROTATE_ENABLED
        )


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
        # semua OFF
        for k in clients:
            clients[k]["status"] = "OFF"

        if state == "ON":
            clients[uid]["status"] = "ON"
            ACTIVE_UNIT = uid
        else:
            ACTIVE_UNIT = None
    return redirect("/")


@app.route("/set_interval", methods=["POST"])
def set_interval():
    global ROTATE_INTERVAL, ROTATE_ENABLED
    seconds = int(request.form.get("seconds", 1500))
    enabled = request.form.get("enabled") == "on"
    ROTATE_INTERVAL = seconds
    ROTATE_ENABLED = enabled
    return redirect("/")


@app.route("/offline_check")
def offline_check():
    now = time.time()
    with LOCK:
        for uid in clients:
            if now - clients[uid]["last_seen"] > 15:
                clients[uid]["status"] = "OFF"
    return "OK"


# ===== ROTATE LOGIC =====
def rotate_clients():
    global ACTIVE_UNIT
    while True:
        time.sleep(ROTATE_INTERVAL)
        if not ROTATE_ENABLED:
            continue

        with LOCK:
            uids = list(clients.keys())
            if not uids:
                continue

            # semua OFF
            for uid in uids:
                clients[uid]["status"] = "OFF"

            # pilih next ON
            if ACTIVE_UNIT not in uids:
                next_idx = 0
            else:
                idx = uids.index(ACTIVE_UNIT)
                next_idx = (idx + 1) % len(uids)

            ACTIVE_UNIT = uids[next_idx]
            clients[ACTIVE_UNIT]["status"] = "ON"


# start background thread
threading.Thread(target=rotate_clients, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
