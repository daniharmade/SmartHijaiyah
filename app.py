import pickle
import cv2
import mediapipe as mp
import numpy as np
import arabic_reshaper
from flask import Flask, render_template, Response, jsonify
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
import sqlite3
from flask import request, redirect, url_for

app = Flask(__name__)

# ==============================
# 1. Load Model & Konfigurasi
# ==============================
model_dict = pickle.load(open('./model/model.p', 'rb'))
model = model_dict['model']

# Global variable untuk menyimpan prediksi terbaru
current_prediction = None

# Inisialisasi MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Label Prediksi
labels_dict = {
    0: 'ا (Alif)', 1: 'ب (Ba)', 2: 'ت (Ta)', 3: 'ث (Tsa)',
    4: 'ج (Jim)', 5: 'ح (Ha)', 6: 'خ (Kha)', 7: 'د (Dal)',
    8: 'ذ (Dzal)', 9: 'ر (Ra)', 10: 'ز (Zay)', 11: 'س (Sin)',
    12: 'ش (Syin)', 13: 'ص (Shad)', 14: 'ض (Dhad)',
    15: 'ط (Tha)', 16: 'ظ (Zha)', 17: 'ع (Ain)',
    18: 'غ (Ghain)', 19: 'ف (Fa)', 20: 'ق (Qaf)',
    21: 'ك (Kaf)', 22: 'ل (Lam)', 23: 'م (Mim)',
    24: 'ن (Nun)', 25: 'و (Waw)', 26: 'ه (Ha)',
    27: 'لا (Lam Alif)', 28: 'ي (Ya)'
}

FONT_PATH = "./static/fonts/NotoNaskhArabic-Regular.ttf"

# ==============================
# 2. Helper Function
# ==============================

def draw_arabic_text(img, text, position, font_size=40):
    try:
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()

        parts = text.split(" ")
        arabic_part = parts[0]
        indo_part = " ".join(parts[1:]) if len(parts) > 1 else ""

        reshaped_text = arabic_reshaper.reshape(arabic_part)
        bidi_text = get_display(reshaped_text)
        final_text = f"{bidi_text} {indo_part}"

        draw.text(position, final_text, font=font, fill=(204, 0, 204))

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    except:
        return img


# ==============================
# 3. Video Stream Generator
# ==============================

def gen_frames():
    global current_prediction

    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        data_aux = []
        x_ = []
        y_ = []

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            min_x, min_y = min(x_), min(y_)

            for i in range(len(x_)):
                data_aux.append(x_[i] - min_x)
                data_aux.append(y_[i] - min_y)

            if len(data_aux) == 42:
                prediction = model.predict([np.asarray(data_aux)])
                predicted_index = int(prediction[0])

                if predicted_index in labels_dict:
                    predicted_character = labels_dict[predicted_index]

                    # Simpan hanya nama huruf (Alif, Ba, dst)
                    current_prediction = predicted_character.split("(")[1].replace(")", "")

                    # Bounding box
                    x1 = int(min(x_) * W) - 10
                    y1 = int(min(y_) * H) - 10
                    x2 = int(max(x_) * W) + 10
                    y2 = int(max(y_) * H) + 10

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 204, 0), 4)

                    frame = draw_arabic_text(
                        frame,
                        predicted_character,
                        (x1, y1 - 40),
                        font_size=40
                    )
        else:
            # Reset kalau tidak ada tangan
            current_prediction = None

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    # TABEL GURU
    conn.execute('''
        CREATE TABLE IF NOT EXISTS guru (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nip TEXT NOT NULL,
            email TEXT NOT NULL,
            spesialisasi TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # TABEL SISWA
    conn.execute('''
        CREATE TABLE IF NOT EXISTS siswa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nisn TEXT NOT NULL,
            kelas TEXT NOT NULL,
            email TEXT
        )
    ''')
    
    # TABEL BELAJAR
    conn.execute('''
    CREATE TABLE IF NOT EXISTS proses_belajar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        siswa_id INTEGER NOT NULL,
        guru_id INTEGER NOT NULL,
        nilai INTEGER NOT NULL,
        tanggal TEXT NOT NULL,
        catatan TEXT,
        FOREIGN KEY (siswa_id) REFERENCES siswa (id),
        FOREIGN KEY (guru_id) REFERENCES guru (id)
    )
    ''')

    conn.commit()
    conn.close()

init_db()

def get_dashboard_stats():
    conn = get_db_connection()

    total_siswa = conn.execute('SELECT COUNT(*) as count FROM siswa').fetchone()['count']
    total_guru = conn.execute('SELECT COUNT(*) as count FROM guru').fetchone()['count']
    total_sesi = conn.execute('SELECT COUNT(*) as count FROM proses_belajar').fetchone()['count']
    # Misal pencapaian = jumlah nilai >= 90
    pencapaian = conn.execute('SELECT COUNT(*) as count FROM proses_belajar WHERE nilai >= 90').fetchone()['count']

    conn.close()
    return {
        'total_siswa': total_siswa,
        'total_guru': total_guru,
        'total_sesi': total_sesi,
        'pencapaian': pencapaian
    }

# ==============================
# 4. Routes
# ==============================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/developer')
def developer():
    return render_template('developer.html')

@app.route('/belajar')
def belajar():
    return render_template('belajar.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_prediction')
def get_prediction():
    global current_prediction
    return jsonify({"prediction": current_prediction})

@app.route('/dashboard')
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard/dashboard.html', stats=stats)

@app.route('/data-guru')
def data_guru():
    conn = get_db_connection()
    gurus = conn.execute('SELECT * FROM guru').fetchall()
    conn.close()
    return render_template('dashboard/data-guru.html', gurus=gurus)

@app.route('/tambah-guru', methods=['POST'])
def tambah_guru():
    nama = request.form['nama']
    nip = request.form['nip']
    email = request.form['email']
    spesialisasi = request.form['spesialisasi']
    status = request.form['status']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO guru (nama, nip, email, spesialisasi, status) VALUES (?, ?, ?, ?, ?)',
        (nama, nip, email, spesialisasi, status)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('data_guru'))

@app.route('/hapus-guru/<int:id>')
def hapus_guru(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM guru WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('data_guru'))

@app.route('/edit-guru/<int:id>', methods=['POST'])
def edit_guru(id):
    nama = request.form['nama']
    nip = request.form['nip']
    email = request.form['email']
    spesialisasi = request.form['spesialisasi']
    status = request.form['status']

    conn = get_db_connection()
    conn.execute('''
        UPDATE guru
        SET nama=?, nip=?, email=?, spesialisasi=?, status=?
        WHERE id=?
    ''', (nama, nip, email, spesialisasi, status, id))
    conn.commit()
    conn.close()

    return redirect(url_for('data_guru'))

@app.route('/data-siswa')
def data_siswa():
    conn = get_db_connection()
    siswas = conn.execute("SELECT * FROM siswa").fetchall()
    conn.close()
    return render_template('dashboard/data-siswa.html', siswas=siswas)

@app.route('/tambah-siswa', methods=['POST'])
def tambah_siswa():
    nama = request.form['nama']
    nisn = request.form['nisn']
    kelas = request.form['kelas']
    email = request.form['email']

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO siswa (nama, nisn, kelas, email) VALUES (?, ?, ?, ?)",
        (nama, nisn, kelas, email)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('data_siswa'))

@app.route('/edit-siswa/<int:id>', methods=['POST'])
def edit_siswa(id):
    nama = request.form['nama']
    nisn = request.form['nisn']
    kelas = request.form['kelas']
    email = request.form['email']

    conn = get_db_connection()
    conn.execute(
        """
        UPDATE siswa
        SET nama=?, nisn=?, kelas=?, email=?
        WHERE id=?
        """,
        (nama, nisn, kelas, email, id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('data_siswa'))

@app.route('/hapus-siswa/<int:id>')
def hapus_siswa(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM siswa WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('data_siswa'))

@app.route('/proses-belajar')
def proses_belajar():
    conn = get_db_connection()

    proses = conn.execute('''
        SELECT pb.*, s.nama as nama_siswa, g.nama as nama_guru
        FROM proses_belajar pb
        JOIN siswa s ON pb.siswa_id = s.id
        JOIN guru g ON pb.guru_id = g.id
        ORDER BY pb.tanggal DESC
    ''').fetchall()

    siswa = conn.execute("SELECT * FROM siswa").fetchall()
    guru = conn.execute("SELECT * FROM guru").fetchall()

    conn.close()

    return render_template(
        'dashboard/proses-belajar.html',
        proses=proses,
        siswa=siswa,
        guru=guru
    )

@app.route('/tambah-proses', methods=['POST'])
def tambah_proses():
    siswa_id = request.form['siswa_id']
    guru_id = request.form['guru_id']
    nilai = request.form['nilai']
    tanggal = request.form['tanggal']
    catatan = request.form['catatan']

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO proses_belajar 
        (siswa_id, guru_id, nilai, tanggal, catatan)
        VALUES (?, ?, ?, ?, ?)
    ''', (siswa_id, guru_id, nilai, tanggal, catatan))

    conn.commit()
    conn.close()

    return redirect('/proses-belajar')

@app.route('/hapus-proses/<int:id>')
def hapus_proses(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM proses_belajar WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/proses-belajar')

@app.route('/edit-proses/<int:id>', methods=['POST'])
def edit_proses(id):
    siswa_id = request.form['siswa_id']
    guru_id = request.form['guru_id']
    nilai = request.form['nilai']
    tanggal = request.form['tanggal']
    catatan = request.form['catatan']

    conn = get_db_connection()
    conn.execute('''
        UPDATE proses_belajar
        SET siswa_id=?, guru_id=?, nilai=?, tanggal=?, catatan=?
        WHERE id=?
    ''', (siswa_id, guru_id, nilai, tanggal, catatan, id))

    conn.commit()
    conn.close()

    return redirect('/proses-belajar')



# ==============================
# Error Handler 404
# ==============================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# ==============================
# 5. Run App
# ==============================

if __name__ == '__main__':
    app.run(debug=True)
