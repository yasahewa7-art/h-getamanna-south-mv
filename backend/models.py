from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

# 1. ශිෂ්‍යයාගේ ස්ථිර තොරතුරු (1 සිට 13 වසර දක්වාම වෙනස් නොවන දත්ත)
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    admission_no = Column(String, unique=True, index=True) # ඇතුළත් වීමේ අංකය (උදා: 2026-001)
    full_name = Column(String)
    parent_name = Column(String)
    parent_phone = Column(String) # SMS / WhatsApp සඳහා

    enrollments = relationship("StudentEnrollment", back_populates="student")

# 2. පන්ති විස්තර (1 සිට 13 වසර දක්වා සියලුම පන්ති)
class SchoolClass(Base):
    __tablename__ = "school_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(Integer) # උදා: 2026
    grade = Column(Integer)         # 1 සිට 13 දක්වා ඕනෑම ශ්‍රේණියක්
    stream = Column(String, default="General") # 1-11: "General" | 12-13: "Science", "Commerce", "Arts", "Tech"
    section = Column(String)        # උදා: "A", "B", "C", "D"
    teacher_name = Column(String)   # පන්ති භාර ගුරුවරයා

# 3. වසරින් වසර ළමයා සිටින පන්තිය සම්බන්ධ කිරීම (1-A සිට 2-D දක්වා හෝ 11-A සිට 12-Science-A දක්වා)
class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    class_id = Column(Integer, ForeignKey("school_classes.id"))
    academic_year = Column(Integer)

    student = relationship("Student", back_populates="enrollments")

# 4. ගුරුවරුන් දෙමාපියන්ට යවන පණිවිඩ (Parent-Teacher Messages)
class ClassMessage(Base):
    __tablename__ = "class_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("school_classes.id"))
    sender_name = Column(String)
    message_text = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
