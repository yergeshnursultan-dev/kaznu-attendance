import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sqlalchemy.orm import Session
from models import Teacher, Student



STUDENTS = [
    ("STU001", "Жанузаков Алибек Серікұлы"),
    ("STU002", "Сейткали Айгерім Маратқызы"),
    ("STU003", "Мұратов Дәурен Асқарұлы"),
    ("STU004", "Қасымова Динара Ерланқызы"),
    ("STU005", "Әлімбеков Ерлан Болатұлы"),
    ("STU006", "Нұрғалиева Зарина Тимурқызы"),
    ("STU007", "Байжанов Тимур Нұрланұлы"),
    ("STU008", "Сатыбалдина Мадина Асқарқызы"),
    ("STU009", "Оразов Асхат Дәуренұлы"),
    ("STU010", "Төлеутаева Камила Нұрқызы"),
    ("STU011", "Ибраев Руслан Ержанұлы"),
    ("STU012", "Ахметова Сания Бекқызы"),
    ("STU013", "Дюсебаев Нурлан Асылбекұлы"),
    ("STU014", "Қожанова Алия Серікқызы"),
    ("STU015", "Серіков Бауыржан Маратұлы"),
    ("STU016", "Байбатырова Айдана Ерланқызы"),
    ("STU017", "Маратов Дамир Алибекұлы"),
    ("STU018", "Сабырова Гүлмира Тимурқызы"),
    ("STU019", "Тасболатов Ержан Нұрланұлы"),
    ("STU020", "Нұрланова Ботагөз Асқарқызы"),
]


def seed_database(db: Session):
    if db.query(Teacher).count() > 0:
        return

    teacher = Teacher(
        username="bekova",
        password="12345",
        name="Бекова Айгүл Серікқызы",
        subject="Деректер қоры",
        group_name="ИС-401",
        room="Ауд. 301",
        schedule_time="09:00 – 10:30",
    )
    db.add(teacher)

    for sid, name in STUDENTS:
        db.add(Student(student_id=sid, name=name, group_name="ИС-401"))

    db.commit()
