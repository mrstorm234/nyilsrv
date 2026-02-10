import socket, requests, time, ipaddress
import pexpect

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
last_status = None
sudo_user = None
sudo_pass = None

# --------------------
# Scan server
# --------------------
def scan_server():
    global server_ip
    for ip in subnet:
        try:
            r = requests.get(f"http://{ip}:{PORT}/ping", timeout=0.5)
            if r.ok and r.json().get("server") == "nyilsrv-server":
                server_ip = str(ip)
                print("[FOUND SERVER]", server_ip)
                return True
        except:
            pass
    return False

# --------------------
# Register
# --------------------
def register():
    global registered
    try:
        r = requests.post(f"http://{server_ip}:{PORT}/register",
                          json={"hostname": hostname, "ip": my_ip}, timeout=2)
        if r.ok:
            registered = True
            print("[REGISTERED]")
    except Exception as e:
        print("[REGISTER ERROR]", e)

# --------------------
# Heartbeat
# --------------------
def heartbeat():
    try:
        requests.post(f"http://{server_ip}:{PORT}/heartbeat", json={"hostname": hostname}, timeout=2)
    except:
        pass

# --------------------
# Get Status from server
# --------------------
def get_status():
    global sudo_user, sudo_pass
    try:
        r = requests.get(f"http://{server_ip}:{PORT}/client_status/{hostname}", timeout=2)
        if r.ok:
            data = r.json()
            sudo_user = data.get("sudo_user")
            sudo_pass = data.get("sudo_pass")
            return data.get("status")
    except:
        pass
    return None

# --------------------
# Run command with sudo password
# --------------------
def run_sudo(cmd):
    child = pexpect.spawn("sudo -S " + cmd, encoding="utf-8")
    child.expect("password")
    child.sendline(sudo_pass)
    child.wait()
    child.close()

# --------------------
# Apply ON/OFF
# --------------------
def apply_status(status):
    global last_status
    if status != last_status:
        print(f"[CLIENT STATUS] {hostname} -> {status}")
        if status == "ON":
            # start NetworkManager
            run_sudo("/bin/systemctl start NetworkManager.service")
            run_sudo("systemctl restart earnapp.service")
        elif status == "OFF":
            run_sudo("systemctl stop earnapp.service")
        last_status = status

# --------------------
# Main Loop
# --------------------
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

        status = get_status()
        if status:
            apply_status(status)

        time.sleep(INTERVAL)

    except Exception as e:
        print("[ERROR]", e)
        server_ip = None
        registered = False
        time.sleep(3)
