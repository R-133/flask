import time
import cv2
from flask import Response
from ultralytics import YOLO
from notification import send_push_notification
from filter_module import get_tokens_by_camera, get_farmland_and_camera_name
from config import Config
import subprocess

# YOLO модел ачааллах
model = YOLO('yolo12n.pt')
model.to('cuda')  # GPU ашиглах
print("YOLO загвар ажиллаж буй төхөөрөмж:", model.device)
# Сүүлийн мэдэгдэл илгээсэн хугацаа хадгалах
last_notification_time = {}

# Label орчуулга
label_translation = {
    'sheep': 'Хонь',
    'cow': 'Үхэр',
    'horse': 'Адуу',
}

# YouTube stream-ээс stream URL авах
def get_youtube_stream_url(youtube_url):
    try:
        output = subprocess.check_output(
            ["streamlink", "--stream-url", youtube_url, "best"],
            stderr=subprocess.STDOUT,
            text=True
        )
        return output.strip()
    except subprocess.CalledProcessError as e:
        print(f"Streamlink алдаа: {e.output}")
        return None

# Гол video feed функц
def video_feed(video_path, camera_id, app):
    def is_youtube_url(url):
        return "youtube.com" in url or "youtu.be" in url

    cap = None

    # Stream эхлүүлэх
    if is_youtube_url(video_path):
        stream_url = get_youtube_stream_url(video_path)
        if not stream_url:
            return "Stream URL олдсонгүй!", 500
        cap = cv2.VideoCapture(stream_url)
    else:
        cap = cv2.VideoCapture(video_path)

    if not cap or not cap.isOpened():
        return "Видео нээж чадсангүй!", 500

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 30) 
    detect_every_n_frames = 1

    def generate():
        frame_count = 5
        with app.app_context():
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        time.sleep(0.5)
                        continue

                    frame_count += 1
                    animals_detected = []
                    animals_detected_mn = set()

                    # Илрүүлэлт хийх
                    if frame_count % detect_every_n_frames == 0:
                        results = model(frame, verbose=False)
                        detections = results[0].boxes
                        names = model.names

                        for detection in detections:
                            cls_id = int(detection.cls[0])
                            label = names[cls_id]

                            if label in label_translation:
                                x1, y1, x2, y2 = map(int, detection.xyxy[0])
                                conf = detection.conf[0]
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                text = f'{label} {conf:.2f}'
                                cv2.putText(frame, text, (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                animals_detected.append(label)
                                animals_detected_mn.add(label_translation[label])

                    current_time = time.time()
                    image_url = None

                    # Push мэдэгдэл илгээх
                    if animals_detected and (
                        camera_id not in last_notification_time or
                        current_time - last_notification_time[camera_id] > 600
                    ):
                        image_filename = f'static/detected/{camera_id}_{int(current_time)}.jpg'
                        cv2.imwrite(image_filename, frame)
                        image_url = f'{Config.BASE_URL}{image_filename}'

                        tokens = get_tokens_by_camera(camera_id)
                        farmland_name, camera_name = get_farmland_and_camera_name(camera_id)
                        farmland_name = farmland_name or f'Farm {camera_id}'
                        camera_name = camera_name or f'Camera {camera_id}'

                        for expo_token in tokens:
                            send_push_notification(
                                expo_token,
                                'Амьтан илэрлээ!',
                                f"Илэрсэн: {', '.join(animals_detected_mn)}",
                                image_url=image_url,
                                farmland=farmland_name,
                                camera=camera_id,
                                animal=', '.join(animals_detected_mn)
                            )

                        last_notification_time[camera_id] = current_time

                    # Frame-г JPEG болгож stream руу дамжуулах
                    ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    if not ret:
                        break

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

            finally:
                cap.release()

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')