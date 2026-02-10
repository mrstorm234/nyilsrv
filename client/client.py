import socket, requests, time, ipaddress, subprocess

PORT = 5000
INTERVAL = 10

hostname = socket.gethostname()

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

my_ip = get_my_ip()
subnet = ipaddress.ip_network(my_ip + "/24", strict=False)

server_ip = None
registered = False

# -------- scan server --------
def scan_server():
    global server_ip
    for ip in subnet:
        try:
            url = f"http://{ip}:{PORT}/ping"
            r = requests.get(url, timeout=0.5)
            if r.ok and r.json().get("server") == "nyilsrv-server":
                server_ip = str(ip)
                print("[FOUND SERVER]", server_ip)
                return True
        except:
            pass
    return False

# -------- register --------
def register():
    global registered
    try:
        r = requests.post(
            f"http://{server_ip}:{PORT}/register",
            json={"hostname": hostname, "ip": my_ip},
            timeout=2
        )
        if r.ok:
            registered = True
            print("[REGISTERED]", r.json())
    except Exception as e:
        print("[REGISTER ERROR]", e)

# -------- heartbeat --------
def heartbeat():
    try:
        requests.post(
            f"http://{server_ip}:{PORT}/heartbeat",
            json={"hostname": hostname},
            timeout=2
        )
    except:
        pass

# -------- get status from server --------
def get_status():
    """Ambil status ON/OFF dari server"""
    try:
        r = requests.get(f"http://{server_ip}:{PORT}/client_status/{hostname}", timeout=2)
        if r.ok:
            return r.json().get("status")  # "ON" atau "OFF"
    except:
        pass
    return None

# -------- execute commands --------
def apply_status(status):
    if status == "ON":
        print("[STATUS] ON -> starting services")
        subprocess.run(["systemctl", "start", "NetworkManager.service"])
        subprocess.run(["sudo", "systemctl", "restart", "earnapp.service"])
    elif status == "OFF":
        print("[STATUS] OFF -> stopping service")
        subprocess.run(["sudo", "systemctl", "stop", "earnapp.service"])

# -------- main loop --------
while True:
    try:
        if not server_ip:
            print("[SCAN] scanning subnet", subnet)
            if not scan_server():
                time.sleep(5)
                continue

        if not registered:
            register()

        heartbeat()

        # cek status dari server
        status = get_status()
        if status:
            apply_status(status)

        time.sleep(INTERVAL)

    except Exception as e:
        print("[ERROR]", e)
        server_ip = None
        registered = False
        time.sleep(3)
