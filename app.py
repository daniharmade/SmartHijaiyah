import pickle
import cv2
import mediapipe as mp
import numpy as np
import arabic_reshaper
from flask import Flask, render_template, Response, jsonify
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display

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


# ==============================
# 4. Routes
# ==============================

@app.route('/')
def index():
    return render_template('index.html')


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


# ==============================
# 5. Run App
# ==============================

if __name__ == '__main__':
    app.run(debug=True)
