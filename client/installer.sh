#!/bin/bash
set -e

echo "[+] Installing NYILSRV Client"

BASE=/opt/nyilsrv-client

sudo apt update
sudo apt install -y python3 python3-venv curl

sudo mkdir -p $BASE
sudo cp client.py $BASE/

cd $BASE

echo "[+] Creating virtualenv"
python3 -m venv venv

echo "[+] Installing python deps"
$BASE/venv/bin/pip install --upgrade pip
$BASE/venv/bin/pip install requests

echo "[+] Installing systemd service"
sudo cp client.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable client
sudo systemctl restart client

echo "[+] NYILSRV Client installed successfully"
