#!/bin/bash
set -e

echo "===================================="
echo " NYILSRV CLIENT INSTALLER"
echo "===================================="

# pastikan dijalankan sebagai root
if [ "$EUID" -ne 0 ]; then
  echo "[!] Jalankan sebagai root: sudo bash installer.sh"
  exit 1
fi

# ambil direktori asli installer.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="/opt/nyilsrv-client"

echo "[+] Script dir   : $SCRIPT_DIR"
echo "[+] Install path : $BASE"

echo "[+] Update system & install system deps"
apt update
apt install -y python3 python3-venv curl

echo "[+] Create install directory"
mkdir -p "$BASE"

echo "[+] Copy client files"
cp "$SCRIPT_DIR/client.py" "$BASE/client.py"
cp "$SCRIPT_DIR/client.service" /etc/systemd/system/client.service

echo "[+] Create virtual environment (if not exists)"
if [ ! -d "$BASE/venv" ]; then
  python3 -m venv "$BASE/venv"
fi

echo "[+] Install python dependencies"
"$BASE/venv/bin/pip" install --upgrade pip
"$BASE/venv/bin/pip" install flask requests

echo "[+] Reload systemd"
systemctl daemon-reload

echo "[+] Enable & start client service"
systemctl enable client
systemctl restart client

echo "===================================="
echo " NYILSRV CLIENT INSTALLED SUCCESS"
echo "===================================="

echo "[i] Check status with:"
echo "    systemctl status client"
echo "    journalctl -u client -f"
