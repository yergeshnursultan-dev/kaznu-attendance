"""
Студент суреттерін тіркеу скрипті (YuNet + SFace).

Қолданысы:
  python enroll_faces.py

Сурет қою ережесі:
  faces/
    STU001.jpg   ← файл аты = student_id
    STU002.jpg
    STU003.png   (jpg, jpeg, png, webp, bmp форматтары)
"""

import cv2
import json
import sys
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE = Path(__file__).parent
FACES_DIR = BASE / "faces"
DB_PATH = BASE / "kaznu_attendance.db"
DET_MODEL = str(BASE / "face_detection_yunet_2023mar.onnx")
REC_MODEL = str(BASE / "face_recognition_sface_2021dec.onnx")
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

sys.path.insert(0, str(BASE))
from models import Base, Student


def main():
    if not FACES_DIR.exists():
        print(f"ҚАТЕ: {FACES_DIR} папкасы жоқ.")
        sys.exit(1)

    images = [f for f in FACES_DIR.iterdir() if f.suffix.lower() in SUPPORTED]
    if not images:
        print(f"Сурет табылмады. {FACES_DIR} папкасына суреттер салыңыз.")
        print("Мысалы: faces/STU001.jpg, faces/STU002.jpg")
        return

    print(f"Табылды: {len(images)} сурет")

    detector = cv2.FaceDetectorYN.create(
        DET_MODEL, "", (640, 640),
        score_threshold=0.5, nms_threshold=0.3, top_k=100,
    )
    recognizer = cv2.FaceRecognizerSF.create(REC_MODEL, "")
    print("YuNet + SFace модельдері дайын.\n")

    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    success, failed, skipped = 0, 0, 0

    for img_path in sorted(images):
        student_id = img_path.stem.upper()
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            print(f"  [{student_id}] DB-де табылмады — өткізілді")
            skipped += 1
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  [{student_id}] Сурет оқылмады")
            failed += 1
            continue

        h, w = img.shape[:2]
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)

        if faces is None or faces.shape[0] == 0:
            print(f"  [{student_id}] Бет табылмады — сурет айқын, жарық болуы керек")
            failed += 1
            continue

        if faces.shape[0] > 1:
            print(f"  [{student_id}] {faces.shape[0]} бет бар — ең үлкені алынды")

        areas = faces[:, 2] * faces[:, 3]
        face = faces[np.argmax(areas)]

        aligned = recognizer.alignCrop(img, face)
        emb = recognizer.feature(aligned).flatten().tolist()

        student.face_embedding = json.dumps(emb)
        db.commit()
        print(f"  [{student_id}] OK → {student.name}")
        success += 1

    db.close()
    print(f"\n{'='*40}")
    print(f"Нәтиже: {success} тіркелді, {failed} қате, {skipped} өткізілді")
    if success > 0:
        print("Сервер жаңарады. Камера студенттерді таниды!")


if __name__ == "__main__":
    main()
