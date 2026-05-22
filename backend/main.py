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


from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import cv2
import base64
import json
import numpy as np
from datetime import datetime, date
from sqlalchemy.orm import Session
from typing import List, Dict

from database import get_db, engine, Base
from models import Teacher, Student, AttendanceRecord
from face_service import FaceRecognitionService
from seed_data import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_database(db)
        count = _load_embeddings(db)
        if count:
            print(f"[Main] {count} student embeddings loaded")
        else:
            print("[Main] No embeddings yet — enroll faces first")
    finally:
        db.close()
    yield


app = FastAPI(title="KazNU Smart Attendance AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

face_service = FaceRecognitionService()
attendance_sockets: Dict[str, List[WebSocket]] = {}


def _load_embeddings(db):
    """DB-дан барлық face embedding-ді face_service.db-ға жүктейді."""
    face_service.db.clear()
    students = db.query(Student).filter(Student.face_embedding.isnot(None)).all()
    for s in students:
        try:
            emb = np.array(json.loads(s.face_embedding))
            face_service.db[s.student_id] = {"name": s.name, "emb": emb}
        except Exception:
            pass
    return len(face_service.db)


# ─── REST API ────────────────────────────────────────────────────────────────

@app.post("/api/login")
async def login(data: dict, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(
        Teacher.username == data.get("username"),
        Teacher.password == data.get("password"),
    ).first()
    if not teacher:
        raise HTTPException(status_code=401, detail="Login or password is incorrect")
    return {
        "teacher_id": teacher.id,
        "name": teacher.name,
        "subject": teacher.subject,
        "group": teacher.group_name,
        "room": teacher.room,
        "schedule_time": teacher.schedule_time,
    }


@app.post("/api/reload-faces")
async def reload_faces(db: Session = Depends(get_db)):
    """СУРЕТТЕР_ТІРКЕУ.bat іске қосқаннан кейін шақырылады — сервер рестартсыз жаңарады."""
    count = _load_embeddings(db)
    return {"loaded": count, "students": list(face_service.db.keys())}


@app.post("/api/debug-match")
async def debug_match(data: dict):
    """base64 фреймі келгенде барлық студенттермен score-ды қайтарады."""
    import base64
    b64 = data.get("frame", "")
    buf = base64.b64decode(b64)
    arr = np.frombuffer(buf, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "frame decode failed")

    dets = face_service.process_frame(frame)
    scores = face_service.debug_scores(frame) if hasattr(face_service, "debug_scores") else {}
    return {"detections": dets, "scores": scores, "db_count": len(face_service.db)}


@app.get("/api/students/{group}")
async def get_students(group: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.group_name == group).order_by(Student.name).all()
    today = date.today()
    records = {
        r.student_id: r
        for r in db.query(AttendanceRecord).filter(AttendanceRecord.date == today).all()
    }
    return [
        {
            "id": s.id,
            "student_id": s.student_id,
            "name": s.name,
            "group": s.group_name,
            "photo_index": idx + 1,   # алфавит бойынша орны (1-ден)
            "status": records[s.id].status if s.id in records else "absent",
            "time": records[s.id].time.strftime("%H:%M") if s.id in records and records[s.id].time else None,
            "confidence": records[s.id].confidence if s.id in records else None,
        }
        for idx, s in enumerate(students)
    ]


@app.post("/api/attendance/reset-today")
async def reset_today(data: dict, db: Session = Depends(get_db)):
    """Сабақ басталғанда бүгінгі топтың барлық жазбаларын тазалайды."""
    group = data.get("group")
    today = date.today()
    students = db.query(Student).filter(Student.group_name == group).all()
    ids = {s.id for s in students}
    deleted = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id.in_(ids),
        AttendanceRecord.date == today,
    ).delete(synchronize_session=False)
    db.commit()
    return {"reset": deleted, "date": str(today)}


@app.put("/api/attendance/update")
async def update_attendance(data: dict, db: Session = Depends(get_db)):
    student_db_id = data.get("id")
    status = data.get("status")
    confidence = data.get("confidence")
    today = date.today()
    now = datetime.now()

    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student_db_id,
        AttendanceRecord.date == today,
    ).first()

    if record:
        record.status = status
        record.updated_at = now
        if confidence is not None:
            record.confidence = confidence
    else:
        record = AttendanceRecord(
            student_id=student_db_id,
            date=today,
            time=now.time(),
            status=status,
            confidence=confidence,
            method=data.get("method", "auto"),
        )
        db.add(record)

    db.commit()
    return {"success": True, "time": now.strftime("%H:%M")}


# ─── Camera WebSocket ─────────────────────────────────────────────────────────

@app.websocket("/ws/camera/{session_id}")
async def camera_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()

    cap = None
    use_demo = True

    # Try camera indices 0..3 (Windows DirectShow)
    for idx in range(4):
        try:
            test = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if test.isOpened():
                ret, _ = test.read()
                if ret:
                    cap = test
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    use_demo = False
                    print(f"[Camera] Camera found: index {idx}")
                    break
                test.release()
        except Exception:
            pass

    if use_demo:
        print("[Camera] No camera found - running DEMO mode")

    frame_count = 0
    try:
        while True:
            if use_demo:
                frame_b64, detections, fw, fh = _demo_frame(frame_count)
            else:
                ret, frame = cap.read()
                if not ret:
                    use_demo = True
                    frame_count += 1
                    await asyncio.sleep(0.1)
                    continue

                fh, fw = frame.shape[:2]
                detections = face_service.process_frame(frame)

                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
                frame_b64 = base64.b64encode(buf).decode()

            try:
                await websocket.send_json({
                    "type": "frame",
                    "frame": frame_b64,
                    "detections": detections,
                    "is_demo": use_demo,
                    "fw": fw,
                    "fh": fh,
                    "ts": datetime.now().strftime("%H:%M:%S"),
                })
            except Exception:
                break

            # Notify attendance WebSockets
            known = [d for d in detections if d.get("status") == "known"]
            if known:
                msg = json.dumps({"type": "detection", "detections": known})
                dead = []
                for ws in attendance_sockets.get(session_id, []):
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    attendance_sockets[session_id].remove(ws)

            frame_count += 1
            await asyncio.sleep(0.1)   # ~10 fps

    except WebSocketDisconnect:
        pass
    finally:
        if cap is not None:
            cap.release()


@app.websocket("/ws/attendance/{session_id}")
async def attendance_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    attendance_sockets.setdefault(session_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        lst = attendance_sockets.get(session_id, [])
        if websocket in lst:
            lst.remove(websocket)


# ─── Demo frame ───────────────────────────────────────────────────────────────

_DEMO_PEOPLE = [
    {"name": "Жанузаков А.",  "sid": "STU001", "conf": 97.3, "bx": 60,  "by": 90,  "w": 110, "h": 130},
    {"name": "Сейткали А.",   "sid": "STU002", "conf": 93.8, "bx": 235, "by": 85,  "w": 110, "h": 130},
    {"name": "Unknown",       "sid": None,     "conf": 41.2, "bx": 415, "by": 100, "w": 110, "h": 130},
    {"name": "Муратов Д.",    "sid": "STU003", "conf": 88.6, "bx": 150, "by": 260, "w": 105, "h": 125},
    {"name": "Касымова Д.",   "sid": "STU004", "conf": 91.2, "bx": 330, "by": 255, "w": 105, "h": 125},
]


def _demo_frame(frame_count: int):
    """Generate demo frame with silhouettes (no text - browser draws labels)"""
    h, w = 480, 640

    frame = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        v = int(212 - (y / h) * 22)
        frame[y] = [v - 14, v - 7, v + 6]

    for x in range(0, w, 50):
        frame[:, x] = np.clip(frame[:, x].astype(int) - 12, 0, 255).astype(np.uint8)
    for y in range(0, h, 50):
        frame[y, :] = np.clip(frame[y, :].astype(int) - 12, 0, 255).astype(np.uint8)

    t = frame_count * 0.05
    detections = []

    for i, p in enumerate(_DEMO_PEOPLE):
        dx = int(4 * np.sin(t + i * 1.4))
        dy = int(3 * np.cos(t * 0.7 + i * 2.0))
        x1, y1 = p["bx"] + dx, p["by"] + dy
        x2, y2 = x1 + p["w"], y1 + p["h"]

        bc = (172, 162, 150) if p["sid"] else (150, 145, 140)
        cv2.ellipse(frame, (x1 + p["w"] // 2, y1 + 28), (27, 33), 0, 0, 360, bc, -1)
        cv2.rectangle(frame, (x1 + 18, y1 + 58), (x1 + p["w"] - 18, y2), (88, 104, 118), -1)

        detections.append({
            "name": p["name"],
            "student_id": p["sid"],
            "confidence": p["conf"],
            "status": "known" if p["sid"] else "unknown",
            "box": [x1, y1, x2, y2],
        })

    scan_y = int((frame_count * 6) % h)
    ov = frame.copy()
    cv2.line(ov, (0, scan_y), (w, scan_y), (0, 80, 180), 1)
    cv2.addWeighted(frame, 0.94, ov, 0.06, 0, frame)

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 83])
    return base64.b64encode(buf).decode(), detections, w, h
