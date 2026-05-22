"""
Камера алдына тұрып, осы скриптті іске қосыңыз.
STU001.jpg-пен сіздің бетіңіздің ұқсастық score-ін көрсетеді.
"""
import cv2
import json
import numpy as np
from sqlalchemy import create_engine, text

# Load DB embedding
engine = create_engine("sqlite:///kaznu_attendance.db")
with engine.connect() as c:
    rows = c.execute(text(
        "SELECT student_id, face_embedding FROM students WHERE face_embedding IS NOT NULL"
    )).fetchall()

if not rows:
    print("Embedding zhok!")
    exit()

db_embeds = {}
for sid, emb_json in rows:
    db_embeds[sid] = np.array(json.loads(emb_json), dtype=np.float32)

det = cv2.FaceDetectorYN.create(
    "face_detection_yunet_2023mar.onnx", "", (640, 640), 0.5, 0.3, 100
)
rec = cv2.FaceRecognizerSF.create("face_recognition_sface_2021dec.onnx", "")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Kamera ashylmady!")
    exit()

print("Kamera ashyldy. Betinizdi korsetiniz... (q — shygyu)")
print()

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    h, w = frame.shape[:2]
    det.setInputSize((w, h))
    _, faces = det.detect(frame)

    if faces is not None and faces.shape[0] > 0:
        try:
            aligned = rec.alignCrop(frame, faces[0])
            emb = rec.feature(aligned).flatten().astype(np.float32)
            e_norm = emb / (np.linalg.norm(emb) + 1e-10)

            print("--- Scores ---")
            for sid, db_emb in db_embeds.items():
                d_norm = db_emb / (np.linalg.norm(db_emb) + 1e-10)
                score = float(np.dot(e_norm, d_norm))
                status = "TANIDY!" if score > 0.33 else "tanymaidy"
                print(f"  {sid}: {score:.4f}  [{status}]")
            print()
        except Exception as e:
            print(f"Qate: {e}")
    else:
        print("Bet tabylmady...")

    cv2.imshow("Tekseru", frame)
    if cv2.waitKey(500) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
