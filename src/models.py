from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    roll_no = Column(String(50))
    admission_no = Column(String(50))
    dob = Column(Date)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    course_code = Column(String(50))


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    faculty_no = Column(String(50))
    department = Column(String(100))


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    is_active = Column(Boolean)
    remarks = Column(String(200))

    subject = relationship("Subject")
    faculty = relationship("Faculty")


class Registry(Base):
    __tablename__ = "registry"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    session_id = Column(Integer, ForeignKey("sessions.id"))
    check_in_time = Column(Time)
    check_out_time = Column(Time)
    late_check_in_reason = Column(String(200))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    department_email = Column(String(100))
    department_name = Column(String(100))
    password = Column(String(200))
    is_verified = Column(Boolean)
