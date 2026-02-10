#!/bin/bash
set -e

echo "[+] Installing NYILSRV Client"

apt update
apt install -y python3 python3-pip curl

pip3 install flask requests

echo "[+] Setup directories"
mkdir -p /opt/nyilclient

echo "[+] Copy client files"
cp client.py /opt/nyilclient/

echo "[+] Install systemd service"
cp client.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable client
systemctl restart client

echo "[✓] Client installed & running"
