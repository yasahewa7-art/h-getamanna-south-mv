from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Float, Boolean
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

# 1. පරිශීලකයන් (Admin, Teacher, Parent Login සඳහා)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # දුරකථන අංකය හෝ ඇතුළත් වීමේ අංකය
    password = Column(String)
    role = Column(String) # "admin", "teacher", "parent"
    full_name = Column(String)
    linked_id = Column(Integer, nullable=True) # Parent නම් student_id, Teacher නම් class_id

# 2. ශිෂ්‍යයාගේ ස්ථිර තොරතුරු (1 - 13 වසර දක්වා)
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    admission_no = Column(String, unique=True, index=True)
    full_name = Column(String)
    parent_name = Column(String)
    parent_phone = Column(String)

    enrollments = relationship("StudentEnrollment", back_populates="student")

# 3. පන්ති විස්තර (1-A සිට 13-Science-A දක්වා)
class SchoolClass(Base):
    __tablename__ = "school_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(Integer)
    grade = Column(Integer)
    stream = Column(String, default="General")
    section = Column(String)
    teacher_name = Column(String)

# 4. වසරින් වසර පන්ති මාරු කිරීම (Class Shuffling)
class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    class_id = Column(Integer, ForeignKey("school_classes.id"))
    academic_year = Column(Integer)

    student = relationship("Student", back_populates="enrollments")

# 5. දෛනික පැමිණීම (Daily Attendance)
class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    class_id = Column(Integer, ForeignKey("school_classes.id"))
    date = Column(Date, default=datetime.date.today)
    is_present = Column(Boolean, default=True) # True = පැමිණ ඇත, False = නොපැමිණ ඇත

# 6. වාර විභාග ලකුණු (Term Exam Marks)
class ExamMark(Base):
    __tablename__ = "exam_marks"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    academic_year = Column(Integer)
    term = Column(Integer) # 1, 2, හෝ 3 වන වාරය
    subject = Column(String)
    marks = Column(Float)

# 7. ගුරු - දෙමාපිය පණිවිඩ (Parent-Teacher Messages)
class ClassMessage(Base):
    __tablename__ = "class_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("school_classes.id"))
    sender_name = Column(String)
    message_text = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
