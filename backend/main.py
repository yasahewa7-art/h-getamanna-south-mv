import csv
import io
import datetime
from typing import Optional
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
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

app = FastAPI(title="H/Getamanna South MV - PowerSchool Style ERP")

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

# පද්ධතිය ආරම්භ වන විට Default Admin ගිණුමක් සෑදීම (Username: admin, Password: 1234)
@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        default_admin = models.User(
            username="admin",
            password="1234",
            role="admin",
            full_name="ප්‍රධාන පරිපාලක (විදුහල්පති)"
        )
        db.add(default_admin)
        db.commit()
    db.close()

# --- Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str # "admin", "teacher", "parent"
    full_name: str
    linked_id: Optional[int] = None

class StudentCreate(BaseModel):
    admission_no: str
    full_name: str
    parent_name: str
    parent_phone: str

class ClassCreate(BaseModel):
    academic_year: int
    grade: int
    stream: Optional[str] = "General"
    section: str
    teacher_name: str

class AssignClass(BaseModel):
    student_id: int
    class_id: int
    academic_year: int

class AttendanceCreate(BaseModel):
    student_id: int
    class_id: int
    is_present: bool

class MarkCreate(BaseModel):
    student_id: int
    academic_year: int
    term: int
    subject: str
    marks: float

class MessageCreate(BaseModel):
    class_id: int
    sender_name: str
    message_text: str

# --- 1. Login & Users API ---
@app.post("/login/")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == req.username,
        models.User.password == req.password
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="පරිශීලක නාමය හෝ මුරපදය වැරදියි!")
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "linked_id": user.linked_id
    }

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    return {"status": "Success", "message": "නව පරිශීලක ගිණුම සාදන ලදී"}

# --- 2. Students & Classes API ---
@app.post("/students/")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/students/")
def get_all_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()

@app.post("/classes/")
def create_class(school_class: ClassCreate, db: Session = Depends(get_db)):
    db_class = models.SchoolClass(**school_class.dict())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

@app.get("/classes/")
def get_all_classes(db: Session = Depends(get_db)):
    return db.query(models.SchoolClass).all()

@app.post("/enroll/")
def enroll_student(enrollment: AssignClass, db: Session = Depends(get_db)):
    db_enroll = models.StudentEnrollment(**enrollment.dict())
    db.add(db_enroll)
    db.commit()
    return {"status": "Success", "message": "ශිෂ්‍යයා නව පන්තියට ඇතුළත් කරන ලදී"}

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
    return {"status": "Completed", "moved_students_count": updated_count, "errors": errors}

# --- 3. Daily Attendance API ---
@app.post("/attendance/")
def mark_attendance(att: AttendanceCreate, db: Session = Depends(get_db)):
    record = models.Attendance(
        student_id=att.student_id,
        class_id=att.class_id,
        date=datetime.date.today(),
        is_present=att.is_present
    )
    db.add(record)
    db.commit()
    return {"status": "Saved", "message": "පැමිණීම සටහන් කරන ලදී"}

@app.get("/attendance/student/{student_id}")
def get_student_attendance(student_id: int, db: Session = Depends(get_db)):
    return db.query(models.Attendance).filter(models.Attendance.student_id == student_id).all()

# --- 4. Exam Marks API ---
@app.post("/marks/")
def add_exam_mark(mark: MarkCreate, db: Session = Depends(get_db)):
    new_mark = models.ExamMark(**mark.dict())
    db.add(new_mark)
    db.commit()
    return {"status": "Saved", "message": "විභාග ලකුණු ඇතුළත් කරන ලදී"}

@app.get("/marks/student/{student_id}")
def get_student_marks(student_id: int, db: Session = Depends(get_db)):
    return db.query(models.ExamMark).filter(models.ExamMark.student_id == student_id).all()

# --- 5. Parent-Teacher Messages API ---
@app.post("/send-message/")
def send_class_message(msg: MessageCreate, db: Session = Depends(get_db)):
    new_msg = models.ClassMessage(**msg.dict())
    db.add(new_msg)
    db.commit()
    return {"status": "Sent", "message": "පන්තියේ දෙමාපියන් වෙත පණිවිඩය යොමු කරන ලදී"}

@app.get("/messages/{class_id}")
def get_messages(class_id: int, db: Session = Depends(get_db)):
    return db.query(models.ClassMessage).filter(models.ClassMessage.class_id == class_id).all()
