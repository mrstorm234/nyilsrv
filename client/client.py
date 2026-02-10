from flask import Flask, request
import socket
import subprocess
import threading
import time
import requests
import os

app = Flask(__name__)

SERVER_PORT = 5000
CONTROL_PORT = 6000
HEARTBEAT_INTERVAL = 30
SCAN_INTERVAL = 10

HOSTNAME = socket.gethostname()
SERVER_IP = None

# =========================
# GET LOCAL IP (LEBIH AKURAT)
# =========================
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

IP_ADDR = get_ip()

# =========================
# FIND SERVER (AUTO SCAN)
# =========================
def find_server():
    try:
        base = ".".join(IP_ADDR.split(".")[:-1])
    except:
        return None

    print("[SCAN] scanning subnet", base + ".0/24")

    for i in range(1, 255):
        ip = f"{base}.{i}"
        try:
            r = requests.get(
                f"http://{ip}:{SERVER_PORT}",
                timeout=0.3
            )
            if r.status_code == 200:
                print("[SCAN] server found:", ip)
                return ip
        except:
            pass
    return None

# =========================
# REGISTER CLIENT (AUTO RETRY)
# =========================
def register_loop():
    global SERVER_IP

    while True:
        if not SERVER_IP:
            SERVER_IP = find_server()

        if SERVER_IP:
            try:
                requests.post(
                    f"http://{SERVER_IP}:{SERVER_PORT}/register",
                    json={
                        "hostname": HOSTNAME,
                        "ip": IP_ADDR
                    },
                    timeout=5
                )
                print("[REGISTER] OK ->", SERVER_IP)
                return
            except:
                print("[REGISTER] failed, retry")

        time.sleep(SCAN_INTERVAL)

# =========================
# HEARTBEAT THREAD
# =========================
def heartbeat():
    global SERVER_IP

    while True:
        if SERVER_IP:
            try:
                requests.post(
                    f"http://{SERVER_IP}:{SERVER_PORT}/heartbeat",
                    json={"hostname": HOSTNAME},
                    timeout=5
                )
            except:
                print("[HB] lost server, rescan")
                SERVER_IP = None

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
    print("[NYILSRV CLIENT]")
    print("Hostname:", HOSTNAME)
    print("IP      :", IP_ADDR)

    threading.Thread(target=register_loop, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()

    app.run("0.0.0.0", CONTROL_PORT)
