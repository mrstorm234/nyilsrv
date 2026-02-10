#!/bin/bash

apt update
apt install -y python3 python3-pip

pip3 install flask requests

mkdir -p /opt/nyilsrv
cp -r server/* /opt/nyilsrv/

cp /opt/nyilsrv/server.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable server
systemctl start server
