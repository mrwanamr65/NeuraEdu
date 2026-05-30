import cv2
import numpy as np
import face_recognition
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import os
import json
import mysql.connector
from datetime import datetime
import logging

logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_or_update_faces(folder_path, class_name):
    json_file = f"./json_files/{class_name}.json"
    os.makedirs("./json_files", exist_ok=True)
    
    stored_data = {}
    if os.path.exists(json_file):
        try:
            with open(json_file, "r") as f:
                content = f.read().strip()
                if content:
                    stored_data = json.loads(content)
                else:
                    print("Folder is empty")
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error reading JSON file {json_file}: {e}")
            stored_data = {}

    current_files = set(os.listdir(folder_path))
    stored_files = set(stored_data.keys())

    new_files = current_files - stored_files
    for filename in new_files:
        student_code = os.path.splitext(filename)[0]
        full_path = os.path.join(folder_path, filename)
        print(f"New image processing {student_code}, path {full_path}")
        try:
            image = face_recognition.load_image_file(full_path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                stored_data[student_code] = {
                    "path": full_path,
                    "encoding": encoding[0].tolist()
                }
            else:
                print(f'No face in {student_code}')
        except Exception as e:
            logging.error(f"Error processing image {full_path}: {e}")

    try:
        with open(json_file, "w") as f:
            json.dump(stored_data, f)
    except Exception as e:
        logging.error(f"Error writing to JSON file {json_file}: {e}")

    known_faces = {code: data["path"] for code, data in stored_data.items()}
    known_encodings = {code: np.array(data["encoding"]) for code, data in stored_data.items()}
    
    return known_faces, known_encodings

def run_camera_detection(folder_path, cncter, class_name, cam_num):
    """تشغيل الكاميرا للكشف عن الطلاب وتحديث قاعدة البيانات."""
    # الاتصال بقاعدة البيانات
    try:
        cursor = cncter.cursor()
    except mysql.connector.Error as e:
        logging.error(f"Failed to connect to database : {e}")
        return

    # تهيئة النماذج
    try:
        model = YOLO(os.path.join('models', 'yolov8n.pt'))
        tracker = DeepSort(max_age=10)
    except Exception as e:
        logging.error(f"Error initializing YOLO or DeepSort: {e}")
        cursor.close()
        cncter.close()
        return

    # تحميل بيانات الوجوه
    known_faces, known_encodings = load_or_update_faces(folder_path, class_name)

    # فتح الكاميرا
    video_capture = cv2.VideoCapture(cam_num)
    if not video_capture.isOpened():
        logging.error(f"Failed to open camera {cam_num}")
        cursor.close()
        cncter.close()
        return

    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                logging.error(f"Failed to read frame from camera {cam_num}")
                break

            # الكشف عن الأشخاص باستخدام YOLO
            results = model(frame)[0]
            detections = []
            faces_to_recognize = []

            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()
                class_id = int(box.cls[0].item())

                if class_id == 0 and confidence > 0.4:  # الكشف عن الأشخاص فقط
                    detections.append(([x1, y1, x2, y2], confidence, class_id))
                    face_crop = frame[y1:y2, x1:x2]
                    faces_to_recognize.append((face_crop, (x1, y1, x2, y2)))

            # تتبع الأشخاص باستخدام DeepSort
            tracks = tracker.update_tracks(detections, frame=frame)

            for track in tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue

                track_id = track.track_id
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # التعرف على الوجوه
            for face_crop, (x1, y1, x2, y2) in faces_to_recognize:
                rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_face)

                name = "Unknown"
                if face_encodings:
                    face_encoding = face_encodings[0]
                    if known_encodings:
                        matches = face_recognition.compare_faces(list(known_encodings.values()), face_encoding)
                        face_distances = face_recognition.face_distance(list(known_encodings.values()), face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            code = list(known_encodings.keys())[best_match_index]
                            today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            try:
                                update = f"UPDATE {class_name} SET last_time_seen = %s WHERE code = %s"
                                cursor.execute(update, (today, str(code)))
                                cncter.commit()
                                name = code
                            except mysql.connector.Error as e:
                                logging.error(f"Error updating database for {code}: {e}")
                    else:
                        print("(known_encodings: empty)")

                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            # عرض الفيديو
            cv2.imshow("Students", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as e:
        logging.error(f"Unexpected error in camera detection: {e}")

    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        cursor.close()
