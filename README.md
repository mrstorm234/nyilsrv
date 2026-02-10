Cara Install SERVER
1️⃣ Clone Repository
git clone https://github.com/mrstorm234/nyilsrv.git
cd nyilsrv/server

2️⃣ Jalankan Installer Server
sudo bash install.sh


Installer akan otomatis:

install dependency Python

setup systemd service

enable auto start saat boot

jalankan server

3️⃣ Cek Status Server
systemctl status server


Pastikan status active (running).

4️⃣ Akses Web Panel

Buka browser:

http://IP_SERVER:5000


Di web panel kamu bisa:

lihat semua client

lihat client ACTIVE / WAITING / OFFLINE

atur waktu rotasi:

25 menit

35 menit

1 jam

2 jam

3 jam

💻 Cara Install CLIENT

Jalankan langkah ini di SETIAP MESIN CLIENT

1️⃣ Clone Repository
git clone https://github.com/mrstorm234/nyilsrv.git
cd nyilsrv/client

2️⃣ Jalankan Installer Client
sudo bash installer.sh


Installer client akan otomatis:

scan server di jaringan (tanpa set IP)

register hostname & IP ke server

install systemd service

auto connect ke server

auto start saat boot

3️⃣ Cek Status Client
systemctl status client


Pastikan status active (running).

🔁 Sistem Rotasi Client

Hanya 1 client aktif dalam satu waktu

Client aktif:

NetworkManager ON

earnapp RESTART

Client lain otomatis:

earnapp STOP

Setelah waktu habis (25m / 35m / 1–3 jam):

server pindah ke client berikutnya

proses berjalan loop otomatis

🔄 Update Server & Client
Update Server
cd nyilsrv
git pull
cd server
sudo bash install.sh

Update Client
cd nyilsrv
git pull
cd client
sudo bash installer.sh

🧪 Troubleshooting
Client tidak muncul di panel

Pastikan satu jaringan dengan server

Cek service client:

systemctl status client

Client OFFLINE

Client mati / reboot

Network bermasalah

Service client tidak berjalan

🔐 Port Yang Digunakan
Service	Port
Web Panel Server	5000
Control / Heartbeat	6000
