import csv
import io
from typing import Optional
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import models

# SQLite Database සෑදීම
SQLALCHEMY_DATABASE_URL = "sqlite:///./getamanna_mv.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="H/Getamanna South MV - Grade 1-13 Parent Teacher System")

# Frontend වෙබ් පිටුවට Backend සමඟ සම්බන්ධ වීමට අවසර දීම (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Data ලබා ගැනීමේ ආකෘති (Schemas)
class StudentCreate(BaseModel):
    admission_no: str
    full_name: str
    parent_name: str
    parent_phone: str

class ClassCreate(BaseModel):
    academic_year: int
    grade: int                 # 1 සිට 13 දක්වා
    stream: Optional[str] = "General" # 1-11: "General" | 12-13: "Science", "Commerce", "Arts", "Tech"
    section: str               # "A", "B", "C", "D"
    teacher_name: str

class AssignClass(BaseModel):
    student_id: int
    class_id: int
    academic_year: int

class MessageCreate(BaseModel):
    class_id: int
    sender_name: str
    message_text: str

# 1. අලුත් ළමයෙක් ඇතුළත් කිරීම
@app.post("/students/")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# 2. පන්තියක් නිර්මාණය කිරීම (1-A සිට 13-Science-A දක්වා)
@app.post("/classes/")
def create_class(school_class: ClassCreate, db: Session = Depends(get_db)):
    db_class = models.SchoolClass(**school_class.dict())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

# 3. ළමයෙක් තනිව පන්තියකට ඇතුළත් කිරීම
@app.post("/enroll/")
def enroll_student(enrollment: AssignClass, db: Session = Depends(get_db)):
    db_enroll = models.StudentEnrollment(**enrollment.dict())
    db.add(db_enroll)
    db.commit()
    return {"status": "Success", "message": "ශිෂ්‍යයා නව පන්තියට ඇතුළත් කරන ලදී"}

# 4. CSV ගොනුවක් මගින් ළමුන් එකවර නව පන්තිවලට මාරු කිරීම (1-13 Bulk Class Shuffling)
@app.post("/bulk-shuffle/")
async def bulk_shuffle_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    decoded = content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    updated_count = 0
    errors = []

    for row in csv_reader:
        admission_no = row["admission_no"].strip()
        year = int(row["academic_year"].strip())
        grade = int(row["grade"].strip())
        stream = row.get("stream", "General").strip() or "General"
        section = row["section"].strip()

        student = db.query(models.Student).filter(models.Student.admission_no == admission_no).first()
        if not student:
            errors.append(f"ශිෂ්‍ය අංකය හමු නොවීය: {admission_no}")
            continue

        target_class = db.query(models.SchoolClass).filter(
            models.SchoolClass.academic_year == year,
            models.SchoolClass.grade == grade,
            models.SchoolClass.stream == stream,
            models.SchoolClass.section == section
        ).first()

        if not target_class:
            errors.append(f"පන්තිය හමු නොවීය: {year} - Grade {grade} ({stream}) - {section}")
            continue

        new_enrollment = models.StudentEnrollment(
            student_id=student.id,
            class_id=target_class.id,
            academic_year=year
        )
        db.add(new_enrollment)
        updated_count += 1

    db.commit()
    return {
        "status": "Completed",
        "moved_students_count": updated_count,
        "errors": errors
    }

# 5. පන්තියේ සියලුම දෙමාපියන්ට පණිවිඩයක් යැවීම
@app.post("/send-message/")
def send_class_message(msg: MessageCreate, db: Session = Depends(get_db)):
    new_msg = models.ClassMessage(**msg.dict())
    db.add(new_msg)
    db.commit()
    return {"status": "Sent", "message": "පන්තියේ දෙමාපියන් වෙත පණිවිඩය යොමු කරන ලදී"}

# 6. දෙමාපියන්ට තම දරුවාගේ පන්තියේ පණිවිඩ බැලීම
@app.get("/messages/{class_id}")
def get_messages(class_id: int, db: Session = Depends(get_db)):
    return db.query(models.ClassMessage).filter(models.ClassMessage.class_id == class_id).all()
