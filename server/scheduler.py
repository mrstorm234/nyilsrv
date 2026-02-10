import json, time, requests, os

BASE = os.path.dirname(__file__)
CLIENT_DB = os.path.join(BASE, "clients.json")
CFG_DB = os.path.join(BASE, "config.json")

def load_clients():
    if not os.path.exists(CLIENT_DB):
        return []
    return json.load(open(CLIENT_DB))

def save_clients(d):
    json.dump(d, open(CLIENT_DB, "w"), indent=2)

def interval_seconds():
    if not os.path.exists(CFG_DB):
        return 1500
    return json.load(open(CFG_DB)).get("interval_seconds", 1500)

def send(ip, mode):
    try:
        requests.post(
            f"http://{ip}:6000/control",
            json={"mode": mode},
            timeout=3
        )
    except:
        pass

last_active_index = -1  # simpan urutan client terakhir yang aktif

while True:
    try:
        clients = load_clients()
        now = time.time()

        # tandai semua OFFLINE jika last_seen terlalu lama
        for c in clients:
            if now - c.get("last_seen", 0) > 90:
                c["state"] = "OFFLINE"
            else:
                c["state"] = "WAITING"
                send(c["ip"], "off")

        # pilih client yang ONLINE untuk ACTIVE
        online = [c for c in clients if c["state"] != "OFFLINE"]
        if online:
            last_active_index = (last_active_index + 1) % len(online)
            active = online[last_active_index]
            active["state"] = "ACTIVE"
            send(active["ip"], "on")

        save_clients(clients)
        print(f"[ROTATE] Active unit: {active['hostname'] if online else 'None'}")
        time.sleep(interval_seconds())

    except Exception as e:
        print("[ERROR]", e)
        time.sleep(5)
