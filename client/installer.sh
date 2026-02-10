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

# direktori installer & target install
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="/opt/nyilsrv-client"

echo "[+] Script dir   : $SCRIPT_DIR"
echo "[+] Install path : $BASE"

# ========================
# Update system & install deps
# ========================
echo "[+] Update system & install system deps"
apt update
apt install -y python3 python3-venv python3-pip curl

# ========================
# Create install directory
# ========================
echo "[+] Create install directory"
mkdir -p "$BASE"

# ========================
# Copy client files
# ========================
echo "[+] Copy client files"
cp "$SCRIPT_DIR/client.py" "$BASE/client.py"
cp "$SCRIPT_DIR/client.service" /etc/systemd/system/client.service

# ========================
# Create virtual environment
# ========================
echo "[+] Create virtual environment (if not exists)"
if [ ! -d "$BASE/venv" ]; then
  python3 -m venv "$BASE/venv"
fi

# ========================
# Install Python dependencies
# ========================
echo "[+] Install python dependencies in venv"
"$BASE/venv/bin/pip" install --upgrade pip
"$BASE/venv/bin/pip" install flask requests pexpect

# ========================
# Update client.service to use venv Python
# ========================
echo "[+] Update client.service to use venv Python"
SERVICE_FILE="/etc/systemd/system/client.service"

# backup original
cp "$SERVICE_FILE" "$SERVICE_FILE.bak"

# replace ExecStart
sed -i "s|ExecStart=.*|ExecStart=$BASE/venv/bin/python $BASE/client.py|" "$SERVICE_FILE"

# ========================
# Reload systemd & enable service
# ========================
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
