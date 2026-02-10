import json, time, requests, os

BASE = os.path.dirname(__file__)
CLIENT_DB = os.path.join(BASE, "clients.json")
CFG_DB = os.path.join(BASE, "config.json")

def load_clients():
    return json.load(open(CLIENT_DB))

def save_clients(d):
    json.dump(d, open(CLIENT_DB, "w"), indent=2)

def interval_seconds():
    return json.load(open(CFG_DB))["interval_seconds"]

def send(ip, mode):
    try:
        requests.post(
            f"http://{ip}:6000/control",
            json={"mode": mode},
            timeout=3
        )
    except:
        pass

while True:
    clients = load_clients()
    now = time.time()

    online = [c for c in clients if now - c["last_seen"] < 90]

    for c in clients:
        c["state"] = "OFFLINE"

    for c in online:
        c["state"] = "WAITING"
        send(c["ip"], "off")

    if online:
        active = online.pop(0)
        active["state"] = "ACTIVE"
        send(active["ip"], "on")
        online.append(active)

    save_clients(clients)

    print("Rotate every", interval_seconds(), "seconds")
    time.sleep(interval_seconds())
