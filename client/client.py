import socket, requests, time, subprocess

PORT = 5000
INTERVAL = 5
hostname = socket.gethostname()
status_on = "OFF"
server_ip = None

# ===== GET LOCAL IP =====
def get_my_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

my_ip = get_my_ip()

# ===== SCAN SERVER =====
def scan_server():
    global server_ip
    import ipaddress
    subnet = ipaddress.ip_network(my_ip + "/24", strict=False)
    for ip in subnet:
        try:
            url = f"http://{ip}:{PORT}/register"
            r = requests.post(url, json={"hostname":hostname,"ip":my_ip}, timeout=0.4)
            if r.ok:
                server_ip = str(ip)
                print("[FOUND SERVER]", server_ip)
                return True
        except:
            pass
    return False

# ===== HEARTBEAT =====
def heartbeat():
    try:
        if server_ip:
            requests.post(f"http://{server_ip}:{PORT}/heartbeat", json={"hostname":hostname}, timeout=2)
    except:
        pass

# ===== UPDATE STATUS =====
def update_status():
    global status_on
    try:
        if server_ip:
            r = requests.get(f"http://{server_ip}:{PORT}/status/{hostname}", timeout=2)
            if r.ok:
                new_status = r.json().get("status","OFF")
                if new_status != status_on:
                    status_on = new_status
                    if status_on=="ON":
                        print("[ON] Execute start commands")
                        subprocess.run(["systemctl","start","NetworkManager.service"])
                        subprocess.run(["sudo","systemctl","restart","earnapp.service"])
                    else:
                        print("[OFF] Execute stop command")
                        subprocess.run(["sudo","systemctl","stop","earnapp.service"])
    except Exception as e:
        print("[ERROR STATUS]", e)

# ===== MAIN LOOP =====
while True:
    try:
        if not server_ip:
            print("[SCAN] scanning subnet...")
            if not scan_server():
                time.sleep(5)
                continue
        heartbeat()
        update_status()
        time.sleep(INTERVAL)
    except Exception as e:
        print("[ERROR]", e)
        server_ip = None
        status_on = "OFF"
        time.sleep(3)
