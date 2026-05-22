import cv2
import json
import numpy as np
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///kaznu_attendance.db")
with engine.connect() as c:
    rows = c.execute(text(
        "SELECT student_id, face_embedding FROM students WHERE face_embedding IS NOT NULL"
    )).fetchall()

print(f"DB-de embedding bar: {len(rows)} student")
if not rows:
    print("KATE: Embedding zhok!")
    exit()

sid, emb_json = rows[0]
db_emb = np.array(json.loads(emb_json))
print(f"{sid} shape={db_emb.shape}  range=[{db_emb.min():.3f}, {db_emb.max():.3f}]")

det = cv2.FaceDetectorYN.create(
    "face_detection_yunet_2023mar.onnx", "", (640, 640), 0.5, 0.3, 100
)
rec = cv2.FaceRecognizerSF.create("face_recognition_sface_2021dec.onnx", "")

img = cv2.imread("faces/STU001.jpg")
if img is None:
    print("KATE: STU001.jpg okulymsady")
    exit()

h, w = img.shape[:2]
det.setInputSize((w, h))
_, faces = det.detect(img)
n = faces.shape[0] if faces is not None else 0
print(f"STU001.jpg sutetten bet: {n}")

if n == 0:
    print("Surette bet tabylmady — basqa sure salynyz")
    exit()

aligned = rec.alignCrop(img, faces[0])
emb_photo = rec.feature(aligned).flatten()
print(f"Photo emb shape={emb_photo.shape}")

# Cosine similarity (manual — constant zhok bolsa da zhumbys isteydi)
score_manual = float(
    np.dot(emb_photo, db_emb) / (np.linalg.norm(emb_photo) * np.linalg.norm(db_emb))
)
print(f"Cosine score (photo vs DB): {score_manual:.4f}")

# OpenCV match
try:
    score_cv = float(rec.match(
        emb_photo.reshape(1, -1), db_emb.reshape(1, -1),
        cv2.FaceRecognizerSF_FR_COSINE,
    ))
    print(f"OpenCV cosine score:       {score_cv:.4f}")
except Exception as e:
    print(f"OpenCV constant katesi: {e}")

print()
print(f"Threshold 0.33  => {'TANIDY' if score_manual > 0.33 else 'TANYMADY'}")
print(f"Threshold 0.25  => {'TANIDY' if score_manual > 0.25 else 'TANYMADY'}")
print(f"Threshold 0.20  => {'TANIDY' if score_manual > 0.20 else 'TANYMADY'}")
