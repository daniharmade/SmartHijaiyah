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
import base64

app = Flask(__name__)

# ==============================
# 1. Load Model & Konfigurasi
# ==============================
hijaiyah_model_dict = pickle.load(open('./model/hijaiyah.p', 'rb'))
hijaiyah_model = hijaiyah_model_dict['model']

sibi_model_dict = pickle.load(open('./model/sibi.p', 'rb'))
sibi_model = sibi_model_dict['model']

bisindo_model_dict = pickle.load(open('./model/bisindo.p', 'rb'))
bisindo_model = bisindo_model_dict['model']

# Global variable untuk menyimpan prediksi terbaru
current_prediction_hijaiyah = None
current_prediction_sibi = None

camera_running = False

# Inisialisasi MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Label Prediksi
labels_hijaiyah = {
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
# CAMERA CONTROL
# ==============================

camera_running = False
cap = None

def start_camera():
    global cap, camera_running

    # Hindari buka camera berulang
    if camera_running:
        return

    try:
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("⚠️ Camera tidak tersedia")
            cap = None
            camera_running = False
            return

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        camera_running = True
        print("✅ Camera berhasil dijalankan")

    except Exception as e:
        print(f"❌ Error membuka camera: {e}")
        cap = None
        camera_running = False


def stop_camera():
    global cap, camera_running

    camera_running = False

    if cap is not None:
        try:
            cap.release()
            print("🛑 Camera dihentikan")
        except Exception as e:
            print(f"❌ Error saat release camera: {e}")

    cap = None

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

def gen_frames_hijaiyah():
    global current_prediction_hijaiyah

    # cap = cv2.VideoCapture(0)

    while camera_running:
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
                prediction = hijaiyah_model.predict([np.asarray(data_aux)])
                predicted_index = int(prediction[0])

                if predicted_index in labels_hijaiyah:
                    predicted_character = labels_hijaiyah[predicted_index]

                    # Simpan hanya nama huruf (Alif, Ba, dst)
                    current_prediction_hijaiyah = predicted_character.split("(")[1].replace(")", "")

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
            current_prediction_hijaiyah = None

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ==============================
# SIBI ALFABET
# ==============================

labels_sibi = {
    0: 'Default', 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5:'E',
    6:'F', 7:'G', 8:'H', 9:'I', 10:'J', 11:'K', 12:'L',
    13:'M', 14:'N', 15:'O', 16:'P', 17:'Q', 18:'R',
    19:'S', 20:'T', 21:'U', 22:'V', 23:'W',
    24:'X', 25:'Y', 26:'Z'
}

def gen_frames_sibi():
    global current_prediction_sibi

    while camera_running:
        success, frame = cap.read()
        if not success:
            break

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            data_aux = []
            x_ = []
            y_ = []

            for hand_landmarks in results.multi_hand_landmarks[:2]:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                for lm in hand_landmarks.landmark:
                    x_.append(lm.x)
                    y_.append(lm.y)

            if x_ and y_:
                min_x = min(x_)
                min_y = min(y_)

                for i in range(len(x_)):
                    data_aux.append(x_[i] - min_x)
                    data_aux.append(y_[i] - min_y)

                if len(data_aux) == 42:
                    prediction = sibi_model.predict([np.asarray(data_aux)])
                    predicted_index = int(prediction[0])

                    if predicted_index in labels_sibi:
                        predicted_character = labels_sibi[predicted_index]
                        current_prediction_sibi = predicted_character

                        x1 = int(min(x_) * W) - 10
                        y1 = int(min(y_) * H) - 10
                        x2 = int(max(x_) * W) + 10
                        y2 = int(max(y_) * H) + 10

                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 204, 0), 4)
                        cv2.putText(frame, predicted_character,
                                    (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_DUPLEX,
                                    1.5, (204, 0, 204), 3)
        else:
            current_prediction_sibi = None

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ==============================
# BISINDO ALFABET (2 TANGAN)
# ==============================

labels_bisindo = {
    0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F',
    6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L',
    12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R',
    18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W',
    23: 'X', 24: 'Y', 25: 'Z'
}

# Tentukan kebutuhan tangan (mayoritas 2 tangan)
hands_required_bisindo = {
    'A': 2, 'B': 2, 'C': 1, 'D': 2, 'E': 1,
    'F': 2, 'G': 2, 'H': 2, 'I': 1, 'J': 1,
    'K': 2, 'L': 1, 'M': 2, 'N': 2, 'O': 1,
    'P': 2, 'Q': 2, 'R': 1, 'S': 2, 'T': 2,
    'U': 1, 'V': 1, 'W': 2, 'X': 2, 'Y': 2, 'Z': 1
}

current_prediction_bisindo = None

def gen_frames_bisindo():
    global current_prediction_bisindo

    expected_features = 84  # 2 tangan × 21 landmark × 2

    while camera_running:
        success, frame = cap.read()
        if not success:
            break

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        data_aux = []
        all_x = []
        all_y = []

        if results.multi_hand_landmarks:
            num_hands = len(results.multi_hand_landmarks)

            # Ambil maksimal 2 tangan
            for hand_landmarks in results.multi_hand_landmarks[:2]:

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                x_ = []
                y_ = []

                for lm in hand_landmarks.landmark:
                    x_.append(lm.x)
                    y_.append(lm.y)

                if x_ and y_:
                    min_x = min(x_)
                    min_y = min(y_)

                    for i in range(len(x_)):
                        data_aux.append(x_[i] - min_x)
                        data_aux.append(y_[i] - min_y)

                    all_x.extend(x_)
                    all_y.extend(y_)

            # 🔥 Kalau cuma 1 tangan → tambahkan padding 0
            if len(data_aux) == 42:
                data_aux.extend([0.0] * 42)

            # Pastikan panjangnya 84
            if len(data_aux) == expected_features:
                try:
                    prediction = bisindo_model.predict([np.asarray(data_aux)])
                    predicted_index = int(prediction[0])

                    if predicted_index in labels_bisindo:
                        predicted_char = labels_bisindo[predicted_index]
                        required = hands_required_bisindo.get(predicted_char, 2)

                        if num_hands >= required:
                            current_prediction_bisindo = predicted_char
                        else:
                            current_prediction_bisindo = None

                        if all_x and all_y:
                            x1 = int(min(all_x) * W) - 10
                            y1 = int(min(all_y) * H) - 10

                            cv2.putText(
                                frame,
                                predicted_char,
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_DUPLEX,
                                1.5,
                                (0, 140, 255),
                                3
                            )
                    else:
                        current_prediction_bisindo = None

                except Exception as e:
                    print("Prediction error BISINDO:", e)
                    current_prediction_bisindo = None
            else:
                current_prediction_bisindo = None
        else:
            current_prediction_bisindo = None

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
# ==============================
# Backend Dashboard
# ==============================
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
            kelas TEXT NOT NULL,
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

# ==============================
# HALAMAN HIJAIYAH
# ==============================

import base64

@app.route('/belajar-hijaiyah')
def belajar_hijaiyah():
    return render_template('belajar_hijaiyah.html')


@app.route('/predict_hijaiyah', methods=['POST'])
def predict_hijaiyah():

    try:

        data = request.json['image']

        # Ambil base64 image
        encoded_data = data.split(',')[1]

        # Convert ke OpenCV image
        np_arr = np.frombuffer(
            base64.b64decode(encoded_data),
            np.uint8
        )

        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(frame_rgb)

        prediction_result = None

        if results.multi_hand_landmarks:

            hand_landmarks = results.multi_hand_landmarks[0]

            data_aux = []
            x_ = []
            y_ = []

            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            min_x = min(x_)
            min_y = min(y_)

            for i in range(len(x_)):
                data_aux.append(x_[i] - min_x)
                data_aux.append(y_[i] - min_y)

            # 21 landmark × 2 = 42 feature
            if len(data_aux) == 42:

                prediction = hijaiyah_model.predict(
                    [np.asarray(data_aux)]
                )

                predicted_index = int(prediction[0])

                if predicted_index in labels_hijaiyah:

                    predicted_character = labels_hijaiyah[predicted_index]

                    # Ambil nama huruf saja
                    prediction_result = (
                        predicted_character
                        .split("(")[1]
                        .replace(")", "")
                    )

        return jsonify({
            "prediction": prediction_result
        })

    except Exception as e:

        print("ERROR predict_hijaiyah:", e)

        return jsonify({
            "prediction": None
        })

# ==============================
# HALAMAN SIBI
# ==============================
@app.route('/belajar-sibi')
def belajar_sibi():
    return render_template('belajar_sibi.html')

@app.route('/predict_sibi', methods=['POST'])
def predict_sibi():

    try:

        data = request.json['image']

        encoded_data = data.split(',')[1]

        np_arr = np.frombuffer(
            base64.b64decode(encoded_data),
            np.uint8
        )

        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(frame_rgb)

        prediction_result = None

        if results.multi_hand_landmarks:

            hand_landmarks = results.multi_hand_landmarks[0]

            data_aux = []
            x_ = []
            y_ = []

            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            min_x = min(x_)
            min_y = min(y_)

            for i in range(len(x_)):
                data_aux.append(x_[i] - min_x)
                data_aux.append(y_[i] - min_y)

            if len(data_aux) == 42:

                prediction = sibi_model.predict(
                    [np.asarray(data_aux)]
                )

                predicted_index = int(prediction[0])

                if predicted_index in labels_sibi:
                    prediction_result = labels_sibi[predicted_index]

        return jsonify({
            "prediction": prediction_result
        })

    except Exception as e:
        print("ERROR predict_sibi:", e)

        return jsonify({
            "prediction": None
        })

# ==============================
# HALAMAN BISINDO
# ==============================

@app.route('/belajar-bisindo')
def belajar_bisindo():
    return render_template('belajar_bisindo.html')


@app.route('/predict_bisindo', methods=['POST'])
def predict_bisindo():

    try:

        data = request.json['image']

        # Ambil base64 image
        encoded_data = data.split(',')[1]

        # Convert ke OpenCV image
        np_arr = np.frombuffer(
            base64.b64decode(encoded_data),
            np.uint8
        )

        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(frame_rgb)

        prediction_result = None

        if results.multi_hand_landmarks:

            data_aux = []
            all_x = []
            all_y = []

            num_hands = len(results.multi_hand_landmarks)

            # Maksimal 2 tangan
            for hand_landmarks in results.multi_hand_landmarks[:2]:

                x_ = []
                y_ = []

                for lm in hand_landmarks.landmark:
                    x_.append(lm.x)
                    y_.append(lm.y)

                if x_ and y_:

                    min_x = min(x_)
                    min_y = min(y_)

                    for i in range(len(x_)):
                        data_aux.append(x_[i] - min_x)
                        data_aux.append(y_[i] - min_y)

                    all_x.extend(x_)
                    all_y.extend(y_)

            # Jika 1 tangan → padding
            if len(data_aux) == 42:
                data_aux.extend([0.0] * 42)

            # Pastikan 84 feature
            if len(data_aux) == 84:

                prediction = bisindo_model.predict(
                    [np.asarray(data_aux)]
                )

                predicted_index = int(prediction[0])

                if predicted_index in labels_bisindo:

                    predicted_char = labels_bisindo[predicted_index]

                    required = hands_required_bisindo.get(
                        predicted_char,
                        2
                    )

                    if num_hands >= required:
                        prediction_result = predicted_char

        return jsonify({
            "prediction": prediction_result
        })

    except Exception as e:

        print("ERROR predict_bisindo:", e)

        return jsonify({
            "prediction": None
        })

# ==============================
# HALAMAN DASHBOARD
# ==============================

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
    kelas = request.form['kelas']
    status = request.form['status']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO guru (nama, nip, email, kelas, status) VALUES (?, ?, ?, ?, ?)',
        (nama, nip, email, kelas, status)
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
    kelas = request.form['kelas']
    status = request.form['status']

    conn = get_db_connection()
    conn.execute('''
        UPDATE guru
        SET nama=?, nip=?, email=?, kelas=?, status=?
        WHERE id=?
    ''', (nama, nip, email, kelas, status, id))
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
# 5. Run App Development
# ==============================

# if __name__ == '__main__':
#     host = "127.0.0.1"
#     port = 5000

#     print("=" * 50)
#     print("✅ Website Berhasil Dijalankan")
#     print(f"🌐 Akses di: http://{host}:{port}/")
#     print("=" * 50)

#     app.run(debug=True, host=host, port=port)

# ==============================
# 5. Run App Deploy
# ==============================

if __name__ == '__main__':
    import os

    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))

    print("=" * 50)
    print("✅ Website Berhasil Dijalankan")
    print(f"🌐 Server running on: {host}:{port}")
    print("=" * 50)

    app.run(host=host, port=port)
