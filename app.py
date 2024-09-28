import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

# Flask app
app = Flask(__name__)

# Model path
model_path = r'C:\Users\manik\Documents\devhack\deepfake\deepfake-detection\lstm_model.h5'

# Load the pre-trained deepfake detection model
lstm_model = load_model(model_path)

# Directory where uploaded videos will be saved temporarily
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max upload size

# Allowed extensions for video files
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename):
    """ Check if the file is an allowed video format """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_video(video_path, frame_size=(112, 112), num_frames=10):
    """ Preprocess the video to prepare it for model input """
    cap = cv2.VideoCapture(video_path)
    
    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate frame indices to capture evenly distributed frames
    frame_indices = np.linspace(0, total_frames - 1, num_frames).astype(int)
    
    for i in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, frame_size)
            frames.append(frame)
        else:
            frames.append(np.zeros((frame_size[0], frame_size[1], 3)))  # Add zero frames if not enough frames

    cap.release()

    frames = np.array(frames).astype('float32') / 255.0
    frames = np.expand_dims(frames, axis=0)

    return frames

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            input_frames = preprocess_video(file_path)
            prediction = lstm_model.predict(input_frames)

            if prediction[0][0] > 0.5:
                result = f"Fake with confidence {prediction[0][0]:.2f}"
            else:
                result = f"Real with confidence {1 - prediction[0][0]:.2f}"

        except Exception as e:
            result = f"Error during processing: {e}"

        return render_template('result.html', result=result)

    return redirect(request.url)

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
