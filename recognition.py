import cv2
import face_recognition
import numpy as np
import mysql.connector
import json
from pyzbar.pyzbar import decode
import requests
import sys
import time

# Database connection parameters
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "gate"
}

def load_encodings_from_database():
    encodings = {}
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute("SELECT user_id, encoding FROM encodings")
        rows = cursor.fetchall()

        for user_id, encoding_data in rows:
            encodings[user_id] = json.loads(encoding_data)

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error loading encodings from the database: {str(e)}")

    return encodings

def authenticate_with_qrcode(user_id):
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        cursor.execute("SELECT hashed_pin FROM face_image WHERE user_id = %s", (user_id,))
        hashed_pin = cursor.fetchone()

        cursor.close()
        db.close()

        if hashed_pin:
            return hashed_pin[0]

    except Exception as e:
        print(f"Error fetching hashed PIN from the database: {str(e)}")

    return None

def main():
    print("[INFO] Start recognition...")

    known_encodings = load_encodings_from_database()
    vs = cv2.VideoCapture(0)
    start_time = time.time()

    while True:
        ret, frame = vs.read()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)

        if not encodings:
            if time.time() - start_time >= 10:
                print("[INFO] Face recognition failed (timeout)")
                requests.post('http://localhost:5000/authentication-failure', data={'user_id': 'unknown'})
                sys.exit()  # Exit the script if no face detected

        for encoding in encodings:
            for user_id, known_encoding_list in known_encodings.items():
                if any(np.linalg.norm(np.array(known_encoding) - encoding) < 0.5 for known_encoding in known_encoding_list):
                    print(f"[INFO] Recognized user: {user_id}")
                    vs.release()
                    cv2.destroyAllWindows()
                    qr_code_authentication(user_id)
                    return  # Exit main loop if recognized

        cv2.imshow("Face Recognition", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q") or time.time() - start_time >= 10:
            break

    vs.release()
    cv2.destroyAllWindows()

def qr_code_authentication(user_id):
    vs_qr = cv2.VideoCapture(0)
    qr_code_detected = False

    start_time = time.time()

    while True:
        if time.time() - start_time >= 10:
            print("[INFO] QR code recognition time out")
            break

        ret_qr, frame_qr = vs_qr.read()
        decoded_objects = decode(frame_qr)

        for obj in decoded_objects:
            if obj.type == 'QRCODE':
                qr_code_detected = True
                scanned_qr_data = obj.data.decode("utf-8")
                hashed_pin = authenticate_with_qrcode(user_id)
                print(f"Scanned QR Data: {scanned_qr_data}")

                if hashed_pin and hashed_pin == scanned_qr_data.split("\nhashed_pin: ")[1]:
                    success_message = 'QR Code Authentication Successful'
                else:
                    success_message = 'QR Code Authentication Failed (PIN Mismatch)'

                requests.post(
                    'http://localhost:5000/authentication-success' if success_message == 'QR Code Authentication Successful' else 'http://localhost:5000/authentication-failure',
                    data={'user_id': user_id})
                print(f"[INFO] {success_message}")
                sys.exit()

        cv2.imshow("QR Code Authentication", frame_qr)
        key_qr = cv2.waitKey(1) & 0xFF

        if key_qr == ord("q"):
            break

    vs_qr.release()
    cv2.destroyAllWindows()

    if not qr_code_detected:
        print("[INFO] No QR code detected")
        requests.post('http://localhost:5000/authentication-failure', data={'user_id': user_id})

if __name__ == "__main__":
    main()