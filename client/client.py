import socket, requests, time, ipaddress, subprocess, os, uuid

PORT = 5000
INTERVAL = 5
UNIT_FILE = "unit.id"

status_on = "OFF"
server_ip = None


# ===== UNIT ID (PERMANENT) =====
def get_unit_id():
    if os.path.exists(UNIT_FILE):
        return open(UNIT_FILE).read().strip()

    uid = str(uuid.uuid4())[:8]
    with open(UNIT_FILE, "w") as f:
        f.write(uid)
    return uid

UNIT_ID = get_unit_id()
HOSTNAME = socket.gethostname()


# ===== SAFE LOCAL IP =====
def get_my_ip():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127."):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("192.168.1.1", 1))
            ip = s.getsockname()[0]
            s.close()
        return ip
    except:
        return None


# ===== WAIT NETWORK =====
def wait_network():
    while True:
        ip = get_my_ip()
        if ip:
            return ip
        time.sleep(3)


my_ip = wait_network()
subnet = ipaddress.ip_network(my_ip + "/24", strict=False)


# ===== SCAN SERVER =====
def scan_server():
    global server_ip
    for ip in subnet:
        try:
            r = requests.post(
                f"http://{ip}:{PORT}/register",
                json={
                    "unit_id": UNIT_ID,
                    "hostname": HOSTNAME,
                    "ip": my_ip
                },
                timeout=0.5
            )
            if r.ok:
                server_ip = str(ip)
                print("[SERVER FOUND]", server_ip)
                return True
        except:
            pass
    return False


# ===== HEARTBEAT =====
def heartbeat():
    try:
        requests.post(
            f"http://{server_ip}:{PORT}/heartbeat",
            json={"unit_id": UNIT_ID},
            timeout=2
        )
    except:
        pass


# ===== STATUS CONTROL =====
def update_status():
    global status_on
    try:
        r = requests.get(
            f"http://{server_ip}:{PORT}/status/{UNIT_ID}",
            timeout=2
        )
        if not r.ok:
            return

        new_status = r.json().get("status", "OFF")

        if new_status != status_on:
            status_on = new_status

            if status_on == "ON":
                subprocess.run(["systemctl", "start", "NetworkManager.service"])
                subprocess.run(["systemctl", "restart", "earnapp.service"])
            else:
                subprocess.run(["systemctl", "stop", "earnapp.service"])

    except:
        pass


# ===== MAIN LOOP =====
while True:
    try:
        if not server_ip:
            scan_server()
            time.sleep(3)
            continue

        heartbeat()
        update_status()
        time.sleep(INTERVAL)

    except:
        server_ip = None
        status_on = "OFF"
        time.sleep(3)
