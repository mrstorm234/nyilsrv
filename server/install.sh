#!/bin/bash
set -e

echo "=== NYILSRV SERVER INSTALLER ==="

APP_DIR=/opt/nyilsrv
VENV_DIR=$APP_DIR/venv

echo "[1/6] Install dependency system"
apt update
apt install -y python3 python3-venv python3-pip

echo "[2/6] Create app directory"
mkdir -p $APP_DIR
cp *.py $APP_DIR/
cp -r templates $APP_DIR/
cp config.json clients.json $APP_DIR/

echo "[3/6] Create Python virtual environment"
python3 -m venv $VENV_DIR

echo "[4/6] Install Python packages"
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install flask requests

echo "[5/6] Install systemd service"
cp server.service /etc/systemd/system/server.service
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable server.service
systemctl restart server.service

echo "[6/6] DONE"
echo "Server running on port 5000"
