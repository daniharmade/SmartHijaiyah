# SmartHijaiyah – Website Interaktif Belajar Huruf Hijaiyah

SmartHijaiyah adalah platform web interaktif berbasis Artificial Intelligence yang dirancang untuk membantu pengguna mempelajari huruf Hijaiyah melalui deteksi gerakan tangan secara real-time menggunakan kamera web dan teknologi Computer Vision.

---

## 📸 Preview Tampilan

### 🏠 Halaman Beranda
<p align="center">
  <img src="preview/beranda.png" width="800">
</p>

### 🎓 Halaman Belajar
<p align="center">
  <img src="preview/belajar.png" width="800">
</p>

### 📊 Halaman Dashboard
<p align="center">
  <img src="preview/dashboard.png" width="800">
</p>

### 🎥 Halaman Proses Belajar
<p align="center">
  <img src="preview/proses-belajar.png" width="800">
</p>

### 📝 Halaman Input Nilai
<p align="center">
  <img src="preview/input-nilai.png" width="800">
</p>

---

## 🌟 Deskripsi Singkat

Proyek ini menyediakan media pembelajaran huruf Hijaiyah yang modern, interaktif, dan mudah diakses.  
Pengguna dapat mempraktikkan gerakan isyarat huruf Hijaiyah di depan kamera, dan sistem akan memberikan hasil prediksi secara langsung menggunakan model Machine Learning.

Website ini dikembangkan sebagai implementasi Computer Vision dan Supervised Learning dalam bidang edukasi berbasis AI.

---

## ✨ Fitur Utama

- 📖 Pembelajaran Huruf Hijaiyah Interaktif  
- 🎥 Deteksi Gerakan Tangan Real-time  
- 🤖 Klasifikasi Huruf Menggunakan Random Forest  
- 🔴 Indikator LIVE Kamera  
- 📝 Menampilkan Huruf Latin dan Arab  
- ✋ Mendukung Deteksi 1 atau 2 Tangan  
- 📱 Desain Responsif (Desktop & Mobile)  
- ❓ FAQ dan Panduan Penggunaan  
- 🖥️ URL Lokal Ditampilkan Saat Aplikasi Dijalankan  

---

## 🛠️ Teknologi yang Digunakan

### Backend
- Python 3.10
- Flask

### Computer Vision
- OpenCV
- MediaPipe (Hand Landmark Detection)

### Machine Learning
- Scikit-learn (Random Forest Classifier)
- NumPy
- Pickle

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap / Tailwind CSS

### Library Tambahan
- Pillow
- arabic-reshaper
- python-bidi

---

## 📁 Struktur Proyek

```
SmartHijaiyah/
├── app.py
├── model/
│   └── model_rf1.p
├── static/
│   ├── css/
│   ├── js/
│   ├── img/
│   │   └── hijaiyah/
├── templates/
│   ├── index.html
│   └── belajar.html
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 🚀 Setup & Installation Guide

> ⚠️ Disarankan menggunakan **Python 3.10** untuk kompatibilitas terbaik.

---

# 💻 Setup di Windows

## 1️⃣ Install Python 3.10

Download dari:
https://www.python.org/downloads/release/python-3100/

Saat install:
- ✅ Centang **Add Python to PATH**
- ✅ Klik **Install Now**

Cek versi:

```bash
python --version
```

---

## 2️⃣ Masuk ke Folder Project

```bash
cd path\ke\SmartHijaiyah
```

Contoh:

```bash
cd D:\Project\SmartHijaiyah
```

---

## 3️⃣ Buat Virtual Environment

```bash
python -m venv venv
```

---

## 4️⃣ Aktifkan Virtual Environment

Command Prompt:

```bash
venv\Scripts\activate
```

PowerShell:

```bash
venv\Scripts\Activate.ps1
```

---

## 5️⃣ Upgrade pip

```bash
pip install --upgrade pip
```

---

## 6️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 7️⃣ Jalankan Aplikasi

```bash
python app.py
```

Buka browser:

```
http://127.0.0.1:5000/
```

---

# 🍎 Setup di macOS / Linux

## 1️⃣ Install Python 3.10 (Jika Belum Ada)

```bash
brew install python@3.10
```

Cek versi:

```bash
python3.10 --version
```

---

## 2️⃣ Masuk ke Folder Project

```bash
cd path/ke/SmartHijaiyah
```

---

## 3️⃣ Buat Virtual Environment

```bash
python3.10 -m venv venv
```

---

## 4️⃣ Aktifkan Virtual Environment

```bash
source venv/bin/activate
```

---

## 5️⃣ Upgrade pip

```bash
pip install --upgrade pip
```

---

## 6️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 7️⃣ Jalankan Aplikasi

```bash
python app.py
```

Buka di browser:

```
http://127.0.0.1:5000/
```

---

# 🔁 Menjalankan Kembali

Windows:
```bash
venv\Scripts\activate
python app.py
```

Mac/Linux:
```bash
source venv/bin/activate
python app.py
```

---

# ❌ Keluar dari Virtual Environment

```bash
deactivate
```

---

# 🛡️ .gitignore (Penting)

Pastikan file `.gitignore` berisi:

```
venv/
__pycache__/
*.pyc
.env
.DS_Store
.vscode/
```

Agar virtual environment tidak ikut ter-push ke repository.

---

# 🧠 Informasi Model Machine Learning

- Model: Random Forest Classifier  
- Input: 84 fitur (2 tangan × 21 landmark × 2 koordinat)  
- Jika hanya 1 tangan terdeteksi → sistem melakukan padding 42 fitur  
- Landmark dinormalisasi agar stabil terhadap posisi dan skala  

---

# ⚠️ Troubleshooting

### Kamera Tidak Muncul
- Pastikan webcam tidak digunakan aplikasi lain
- Periksa izin akses kamera di browser
- Restart aplikasi

### Prediksi Tidak Akurat
- Gunakan pencahayaan cukup
- Pastikan tangan terlihat jelas
- Hindari background ramai
- Jangan bergerak terlalu cepat

### Error Library / Dependency
- Pastikan menggunakan Python 3.10
- Gunakan virtual environment
- Upgrade pip sebelum install

---

# 🎓 Tujuan Pengembangan

- Media pembelajaran huruf Hijaiyah berbasis AI  
- Implementasi Computer Vision  
- Implementasi Supervised Learning  
- Proyek penelitian / tugas akhir  

---

# 🙌 Kontribusi

Masukan dan saran sangat terbuka untuk pengembangan lebih lanjut.

---

# 📜 Lisensi

Proyek ini bersifat open-source.  
Detail lisensi akan ditambahkan pada pembaruan berikutnya.

---

# 🙏 Ucapan Terima Kasih

Terima kasih kepada:
- Flask
- OpenCV
- MediaPipe
- Scikit-learn
- Komunitas Open Source

---

⭐ Jika project ini bermanfaat, jangan lupa beri star di repository!
