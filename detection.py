from flask import Response
from flask_socketio import emit
import cv2
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture('input.mp4')

def video_feed(socketio):
    def generate():
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

            results = model(frame)
            detections = results[0].boxes
            names = model.names
            animals_detected = []

            for detection in detections:
                cls_id = int(detection.cls[0])
                label = names[cls_id]
                if label in ['sheep', 'cow', 'horse', 'bird']:
                    x1, y1, x2, y2 = map(int, detection.xyxy[0])
                    conf = detection.conf[0]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    text = f'{label} {conf:.2f}'
                    cv2.putText(frame, text, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0),2)
                    animals_detected.append(label)

            if animals_detected:
                socketio.emit('animal_detected', {'animals': animals_detected})

            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                break
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
