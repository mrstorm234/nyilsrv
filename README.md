inggal copy–paste, langsung pakai

# NyilSrv – Server & Client Rotasi Otomatis

NyilSrv adalah sistem **Server–Client berbasis Linux** dengan mekanisme **rotasi otomatis**.
Server bertugas sebagai pengendali utama, sedangkan client akan **bergantian aktif**
sesuai waktu rotasi yang diatur melalui **Web Panel**.

Sistem ini berjalan dalam **satu jaringan lokal** dan **tidak memerlukan setting IP manual**.

---

## 🚀 Cara Install SERVER

Server adalah pusat kontrol yang:
- Menyimpan dan mengatur daftar client
- Mengatur rotasi client
- Menyediakan Web Panel monitoring

### 1️⃣ Clone Repository & Masuk Folder Server
```bash
git clone https://github.com/mrstorm234/nyilsrv.git
cd nyilsrv/server

2️⃣ Jalankan Installer Server
sudo bash install.sh


Installer server akan otomatis:

Install dependency Python

Membuat systemd service server

Mengaktifkan auto start saat boot

Menjalankan server

3️⃣ Cek Status Server
systemctl status server


Pastikan status:

active (running)

4️⃣ Akses Web Panel

Buka browser:

http://IP_SERVER:5000


Di Web Panel:

Lihat semua client

Status client: ACTIVE / WAITING / OFFLINE

Atur waktu rotasi:

25 menit

35 menit

1 jam

2 jam

3 jam

💻 Cara Install CLIENT

Client adalah mesin yang akan dikontrol server dan bergantian aktif.

⚠️ Jalankan langkah ini di SETIAP MESIN CLIENT

1️⃣ Clone Repository & Masuk Folder Client
git clone https://github.com/mrstorm234/nyilsrv.git
cd nyilsrv/client

2️⃣ Jalankan Installer Client
sudo bash installer.sh

cd nyilsrv/client
chmod +x installer.sh
sudo bash installer.sh


Installer client akan otomatis:

Mencari server di jaringan

Register hostname & IP ke server

Membuat systemd service client

Auto connect ke server

Auto start saat boot

3️⃣ Cek Status Client
systemctl status client


Pastikan status:

active (running)

▶️ Cara Menjalankan / Menghentikan Service
Menjalankan Server
sudo systemctl start server

Menjalankan Client
sudo systemctl start client

Menghentikan Service
sudo systemctl stop server
sudo systemctl stop client

Restart Service
sudo systemctl restart server
sudo systemctl restart client

🔁 Cara Kerja Rotasi Client

Dalam satu waktu hanya 1 client aktif

Client aktif:

NetworkManager ON

earnapp RESTART

Client lain:

earnapp STOP

Alur Rotasi:

Server memilih 1 client sebagai ACTIVE

Client berjalan sesuai waktu rotasi

Setelah waktu habis, server pindah ke client berikutnya

Proses berjalan loop otomatis

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
Client Tidak Muncul di Web Panel

Pastikan satu jaringan dengan server

Pastikan service client berjalan:

systemctl status client

Status Client OFFLINE

Penyebab umum:

Client mati / reboot

Network bermasalah

Service client tidak berjalan

🔐 Port Yang Digunakan
Service	Port
Web Panel Server	5000
Control / Heartbeat	6000
✅ Catatan

Jalankan sebagai root / sudo

Buka firewall port 5000 dan 6000

Sistem berjalan full otomatis

