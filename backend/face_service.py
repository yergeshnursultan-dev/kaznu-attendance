import sys
import io
import os

# Fix Windows console encoding for Kazakh characters
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

MODEL_DIR = Path(__file__).parent
DET_MODEL = str(MODEL_DIR / "face_detection_yunet_2023mar.onnx")
REC_MODEL = str(MODEL_DIR / "face_recognition_sface_2021dec.onnx")

THRESHOLD = 0.33   # SFace cosine threshold (0.33 = OpenCV ұсынысы)


class FaceRecognitionService:
    def __init__(self):
        self.detector = None
        self.recognizer = None
        self.db: Dict[str, Dict] = {}   # sid -> {name, emb}
        self._load_models()

    def _load_models(self):
        try:
            self.detector = cv2.FaceDetectorYN.create(
                DET_MODEL, "", (640, 640),
                score_threshold=0.6, nms_threshold=0.3, top_k=100,
            )
            print("[FaceService] YuNet detector loaded OK")
        except Exception as e:
            print(f"[FaceService] YuNet load failed: {e}")

        try:
            self.recognizer = cv2.FaceRecognizerSF.create(REC_MODEL, "")
            print("[FaceService] SFace recognizer loaded OK")
        except Exception as e:
            print(f"[FaceService] SFace load failed: {e}")

    def get_embedding(self, frame: np.ndarray) -> np.ndarray | None:
        """Return embedding of the largest face in frame (for enrollment)."""
        faces = self._detect(frame)
        if faces is None or faces.shape[0] == 0:
            return None
        face = self._biggest(faces)
        aligned = self.recognizer.alignCrop(frame, face)
        emb = self.recognizer.feature(aligned)
        return emb.flatten()

    def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        if self.detector is None:
            return self._haar_fallback(frame)

        faces = self._detect(frame)
        if faces is None or faces.shape[0] == 0:
            return []

        results = []
        for face in faces:
            x, y, w, h = [int(v) for v in face[:4]]
            x1, y1, x2, y2 = x, y, x + w, y + h

            match = None
            if self.recognizer is not None and self.db:
                try:
                    aligned = self.recognizer.alignCrop(frame, face)
                    emb = self.recognizer.feature(aligned).flatten()
                    match = self._match(emb)
                except Exception:
                    pass

            if match:
                results.append({
                    "name": match["name"],
                    "student_id": match["student_id"],
                    "confidence": match["confidence"],
                    "status": "known",
                    "box": [x1, y1, x2, y2],
                })
            else:
                results.append({
                    "name": "Unknown",
                    "student_id": None,
                    "confidence": 0.0,
                    "status": "unknown",
                    "box": [x1, y1, x2, y2],
                })
        return results

    def _detect(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(frame)
        return faces

    def _biggest(self, faces: np.ndarray):
        areas = faces[:, 2] * faces[:, 3]
        return faces[np.argmax(areas)]

    def _match(self, emb: np.ndarray):
        # OpenCV 4.13 float32/float64 type bug bypass — manual cosine similarity
        e = emb.astype(np.float32)
        e_norm = e / (np.linalg.norm(e) + 1e-10)

        best_score, best = 0.0, None
        for sid, data in self.db.items():
            d = data["emb"].astype(np.float32)
            d_norm = d / (np.linalg.norm(d) + 1e-10)
            score = float(np.dot(e_norm, d_norm))
            if score > THRESHOLD and score > best_score:
                best_score = score
                best = {
                    "name": data["name"],
                    "student_id": sid,
                    "confidence": round(score * 100, 1),
                }
        return best

    def debug_scores(self, frame: np.ndarray) -> dict:
        """Камерадағы бет пен барлық студент arasyndagy score-ды қайтарады."""
        if self.detector is None or self.recognizer is None or not self.db:
            return {}
        faces = self._detect(frame)
        if faces is None or faces.shape[0] == 0:
            return {"error": "no_face_detected"}
        try:
            aligned = self.recognizer.alignCrop(frame, faces[0])
            emb = self.recognizer.feature(aligned).flatten().astype(np.float32)
            e_norm = emb / (np.linalg.norm(emb) + 1e-10)
            result = {}
            for sid, data in self.db.items():
                d = data["emb"].astype(np.float32)
                d_norm = d / (np.linalg.norm(d) + 1e-10)
                score = float(np.dot(e_norm, d_norm))
                result[sid] = round(score, 4)
            return result
        except Exception as e:
            return {"error": str(e)}

    def _haar_fallback(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            clf = cv2.CascadeClassifier(cascade)
            faces = clf.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
            return [
                {
                    "name": "Unknown",
                    "student_id": None,
                    "confidence": 0.0,
                    "status": "unknown",
                    "box": [int(x), int(y), int(x + w), int(y + h)],
                }
                for x, y, w, h in (faces if len(faces) > 0 else [])
            ]
        except Exception:
            return []
