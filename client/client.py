from flask import Flask, request
import socket
import subprocess
import threading
import time
import requests
import os
import sys

app = Flask(__name__)

SERVER_PORT = 5000
CONTROL_PORT = 6000
HEARTBEAT_INTERVAL = 30

HOSTNAME = socket.gethostname()

def get_ip():
    try:
        return socket.gethostbyname(HOSTNAME)
    except:
        return "0.0.0.0"

IP_ADDR = get_ip()
SERVER_IP = None


# =========================
# FIND SERVER (AUTO SCAN)
# =========================
def find_server():
    try:
        base = ".".join(IP_ADDR.split(".")[:-1])
    except:
        return None

    for i in range(1, 255):
        ip = f"{base}.{i}"
        try:
            r = requests.get(f"http://{ip}:{SERVER_PORT}", timeout=0.25)
            if r.status_code == 200:
                return ip
        except:
            pass
    return None


# =========================
# REGISTER CLIENT
# =========================
def register():
    global SERVER_IP
    SERVER_IP = find_server()

    if not SERVER_IP:
        print("Server not found")
        return

    try:
        requests.post(
            f"http://{SERVER_IP}:{SERVER_PORT}/register",
            json={
                "hostname": HOSTNAME,
                "ip": IP_ADDR
            },
            timeout=3
        )
        print("Registered to server:", SERVER_IP)
    except:
        print("Register failed")


# =========================
# HEARTBEAT THREAD
# =========================
def heartbeat():
    while True:
        if SERVER_IP:
            try:
                requests.post(
                    f"http://{SERVER_IP}:{SERVER_PORT}/heartbeat",
                    json={"hostname": HOSTNAME},
                    timeout=3
                )
            except:
                pass
        time.sleep(HEARTBEAT_INTERVAL)


# =========================
# CONTROL FROM SERVER
# =========================
@app.route("/control", methods=["POST"])
def control():
    data = request.json
    mode = data.get("mode")

    if mode == "off":
        print("MODE OFF")
        subprocess.call(["systemctl", "stop", "earnapp.service"])

    elif mode == "on":
        print("MODE ON")
        subprocess.call(["systemctl", "start", "NetworkManager.service"])
        subprocess.call(["systemctl", "restart", "earnapp.service"])

    return {"ok": 1}


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    register()
    threading.Thread(target=heartbeat, daemon=True).start()
    app.run("0.0.0.0", CONTROL_PORT)
