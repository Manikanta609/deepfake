import sys
import cv2
import numpy as np
import tensorflow as tf

# Load your trained LSTM model
model = tf.keras.models.load_model('lstm_model.h5')

def extract_frames(video_path, num_frames=10):  # Default to 10 frames
    cap = cv2.VideoCapture(video_path)
    frames = []  # Initialize frames as an empty list
    count = 0

    while cap.isOpened() and count < num_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (112, 112))  # Resize to match your model input
        frames.append(frame)
        count += 1

    cap.release()
    return np.array(frames)

def detect_deepfake(video_path):
    frames = extract_frames(video_path)  # Extract frames from the video
    if len(frames) == 0:
        return "🚨 Error: No frames extracted. Please check the video file!"

    # Ensure the frames shape matches the model input
    frames = np.expand_dims(frames, axis=0)  # Add batch dimension
    prediction = model.predict(frames)  # Adjust according to your model input shape
    
    # Get the probability for a more nuanced response
    probability = prediction[0][0]
    if probability < 0.5:
        return f" The video is classified as **fake** with a confidence of **{(1 - probability) * 100:.2f}%**!"
    else:
        return f" The video is classified as **real** with a confidence of **{probability * 100:.2f}%**!"

if __name__ == "__main__":
    video_file = sys.argv[1]
    result = detect_deepfake(video_file)
    print(result)
