import time
from flask import Response
import cv2
from ultralytics import YOLO
from notification import send_push_notification
from filter_module import get_tokens_by_camera, get_farmland_and_camera_name
from config import Config

model = YOLO('yolov8n.pt')

# Мэдэгдэл илгээх хязгаарлалт
last_notification_time = {}
label_translation = {
    'sheep': 'Хонь',
    'cow': 'Үхэр',
    'horse': 'Адуу'
}

animals_detected_mn = set()  # давхардалгүй цуглуулах

def video_feed(video_path, camera_id, app):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # real-time болгох optimization

    def generate():
        with app.app_context(): 
            while True:
                animals_detected_mn.clear()  # Clear animals from the previous frame
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()

                results = model(frame, verbose=False)
                detections = results[0].boxes
                names = model.names
                animals_detected = []

                for detection in detections:
                    cls_id = int(detection.cls[0])
                    label = names[cls_id]
                    if label in label_translation:
                        x1, y1, x2, y2 = map(int, detection.xyxy[0])
                        conf = detection.conf[0]
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        text = f'{label} {conf:.2f}'
                        cv2.putText(frame, text, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                        animals_detected.append(label)
                        animals_detected_mn.add(label_translation[label]) 

                image_url = None
                current_time = time.time()  

                if animals_detected:
                    # notification хэзээ илгээхийг шалгах
                    if camera_id not in last_notification_time or current_time - last_notification_time[camera_id] > 120:
                        # Илэрсэн кадрыг хадгалах
                        image_filename = f'static/detected/{camera_id}_{int(current_time)}.jpg'
                        cv2.imwrite(image_filename, frame)
                        image_url = f'{Config.BASE_URL}{image_filename}'
                        print("image url: ", image_url)

                        tokens = get_tokens_by_camera(camera_id)
                        farmland_name, camera_name = get_farmland_and_camera_name(camera_id)
                        if not farmland_name:
                            farmland_name = f'Farm {camera_id}'
                        if not camera_name:
                            camera_name = f'Camera {camera_id}'

                        for expo_token in tokens:
                            send_push_notification(
                                expo_token,
                                'Амьтан илэрлээ!',
                                f"Илэрсэн: {', '.join(animals_detected_mn)}",
                                image_url=image_url,
                                farmland=farmland_name,
                                camera=camera_name,
                                animal=', '.join(animals_detected_mn)
                            )

                        # notification илгээсэн цагийг шинэчлэх
                        last_notification_time[camera_id] = current_time

                # Хэрвээ кадрыг jpeg болгож encode хийхэд амжилтгүй болбол loop зогсооно
                ret, jpeg = cv2.imencode('.jpg', frame)
                if not ret:
                    break

                # stream хийх хэсэг
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
