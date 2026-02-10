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
            r = requests.get(url, timeout=0.4)
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
    r = requests.post(
        f"http://{server_ip}:{PORT}/register",
        json={
            "hostname": hostname,
            "ip": my_ip
        },
        timeout=2
    )
    if r.ok:
        registered = True
        print("[REGISTERED]")

# -------- heartbeat --------

def heartbeat():
    requests.post(
        f"http://{server_ip}:{PORT}/heartbeat",
        json={"hostname": hostname},
        timeout=2
    )

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
        time.sleep(INTERVAL)

    except Exception as e:
        print("[ERROR]", e)
        server_ip = None
        registered = False
        time.sleep(3)
