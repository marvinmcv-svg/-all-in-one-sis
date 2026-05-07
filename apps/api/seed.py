"""
Database seed script for development.
Creates sample data for testing the All-in-One SIS.
"""
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session, engine
from models.base import Base
from models.tenant import Tenant, School
from models.person import User, Person, UserRole
from models.student import Student, Enrollment, StudentStatus
from models.teacher import Teacher, TeacherAssignment
from models.parent import Parent
from models.academic import (
    AcademicTerm, GradeLevel, Department, Subject, 
    ClassSection, ClassSubject
)
from models.gradebook import GradingSystem, GradeScale, ExamType
from models.attendance import AttendanceRecord, AttendanceStatus
from core.security import get_password_hash


async def seed_tenant(db: AsyncSession):
    """Create tenant and school"""
    tenant = Tenant(
        name="Demo School District",
        slug="demo",
        is_active=True
    )
    db.add(tenant)
    await db.flush()
    
    school = School(
        tenant_id=tenant.id,
        name="Demo High School",
        address="123 Education St",
        phone="555-0100",
        email="admin@demo.edu",
        timezone="America/New_York",
        academic_year="2025-2026",
        is_active=True
    )
    db.add(school)
    await db.flush()
    
    return tenant, school


async def seed_academic_structure(db: AsyncSession, school_id: int):
    """Create academic structure"""
    # Academic Term
    term = AcademicTerm(
        school_id=school_id,
        name="2025-2026 Term 1",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 1, 15),
        is_current=True
    )
    db.add(term)
    await db.flush()
    
    # Grade Levels
    grades = []
    for i, name in enumerate(["Grade 9", "Grade 10", "Grade 11", "Grade 12"]):
        grade = GradeLevel(
            school_id=school_id,
            name=name,
            code=f"G{9+i}",
            sequence=i+1
        )
        db.add(grade)
        grades.append(grade)
    await db.flush()
    
    # Set next grade relationships
    for i in range(len(grades) - 1):
        grades[i].next_grade_id = grades[i + 1].id
    await db.flush()
    
    # Departments
    departments = []
    for name in ["Mathematics", "Science", "English", "History", "Physical Education"]:
        dept = Department(
            school_id=school_id,
            name=name
        )
        db.add(dept)
        departments.append(dept)
    await db.flush()
    
    # Subjects
    subjects = []
    subject_data = [
        ("Mathematics", "MATH", 4.0),
        ("Physics", "PHYS", 4.0),
        ("Chemistry", "CHEM", 4.0),
        ("Biology", "BIOL", 4.0),
        ("English Literature", "ENGL", 3.0),
        ("English Writing", "ENGW", 3.0),
        ("World History", "HIST", 3.0),
        ("US History", "USHIST", 3.0),
        ("Physical Education", "PE", 1.0),
        ("Computer Science", "CS", 3.0),
    ]
    for name, code, credits in subject_data:
        subject = Subject(
            school_id=school_id,
            name=name,
            code=code,
            credit_hours=credits,
            subject_type="theory"
        )
        db.add(subject)
        subjects.append(subject)
    await db.flush()
    
    # Class Sections
    sections = []
    for grade_idx, grade in enumerate(grades):
        for sec_num in range(2):  # A and B
            section = ClassSection(
                school_id=school_id,
                grade_level_id=grade.id,
                name=f"Section {chr(65+sec_num)}",  # A, B
                room_number=f"Room {100 + grade_idx * 2 + sec_num}",
                capacity=30,
                academic_term_id=term.id
            )
            db.add(section)
            sections.append((section, grade))
    await db.flush()
    
    return term, grades, departments, subjects, sections


async def seed_grading_system(db: AsyncSession, school_id: int):
    """Create default grading system"""
    gs = GradingSystem(
        school_id=school_id,
        name="Standard 10-Point",
        grading_type="letter",
        is_default=True
    )
    db.add(gs)
    await db.flush()
    
    scales = [
        ("A+", 90, 100, 4.0),
        ("A", 85, 89, 3.9),
        ("B+", 80, 84, 3.5),
        ("B", 75, 79, 3.0),
        ("C+", 70, 74, 2.5),
        ("C", 65, 69, 2.0),
        ("D", 60, 64, 1.0),
        ("F", 0, 59, 0.0),
    ]
    
    for letter, min_pct, max_pct, point in scales:
        scale = GradeScale(
            grading_system_id=gs.id,
            letter=letter,
            min_percentage=min_pct,
            max_percentage=max_pct,
            grade_point=point
        )
        db.add(scale)
    await db.flush()
    
    return gs


async def seed_admin_user(db: AsyncSession, tenant_id: int, school_id: int):
    """Create admin user"""
    person = Person(
        tenant_id=tenant_id,
        first_name="System",
        last_name="Administrator",
        gender="other"
    )
    db.add(person)
    await db.flush()
    
    user = User(
        tenant_id=tenant_id,
        email="admin@demo.edu",
        password_hash=get_password_hash("admin123"),
        role=UserRole.admin,
        is_active=True
    )
    db.add(user)
    await db.flush()
    
    person.user_id = user.id
    await db.flush()
    
    return user


async def seed_teachers(db: AsyncSession, tenant_id: int, school_id: int, departments: list, subjects: list, term_id: int):
    """Create sample teachers"""
    teachers = []
    teacher_data = [
        ("John", "Smith", "john@demo.edu", "Mathematics"),
        ("Sarah", "Johnson", "sarah@demo.edu", "Science"),
        ("Michael", "Williams", "michael@demo.edu", "English"),
        ("Emily", "Brown", "emily@demo.edu", "History"),
        ("David", "Jones", "david@demo.edu", "Physical Education"),
        ("Lisa", "Davis", "lisa@demo.edu", "Computer Science"),
    ]
    
    for first, last, email, dept_name in teacher_data:
        person = Person(
            tenant_id=tenant_id,
            first_name=first,
            last_name=last,
            gender="female" if first in ["Sarah", "Emily", "Lisa"] else "male"
        )
        db.add(person)
        await db.flush()
        
        user = User(
            tenant_id=tenant_id,
            email=email,
            password_hash=get_password_hash("teacher123"),
            role=UserRole.teacher,
            is_active=True
        )
        db.add(user)
        await db.flush()
        
        person.user_id = user.id
        await db.flush()
        
        dept = next(d for d in departments if d.name == dept_name)
        teacher = Teacher(
            tenant_id=tenant_id,
            person_id=person.id,
            employee_id=f"EMP-2025-{len(teachers)+1:03d}",
            department_id=dept.id,
            designation="Teacher",
            hire_date=date(2020, 9, 1)
        )
        db.add(teacher)
        teachers.append((teacher, user))
        await db.flush()
    
    return teachers


async def seed_students(db: AsyncSession, tenant_id: int, school_id: int, sections: list, term_id: int):
    """Create sample students"""
    students = []
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", 
                   "Michael", "Linda", "William", "Elizabeth", "David", "Barbara",
                   "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez"]
    
    student_num = 1
    for section, grade in sections:
        for i in range(5):  # 5 students per section
            first = random.choice(first_names)
            last = random.choice(last_names)
            
            person = Person(
                tenant_id=tenant_id,
                first_name=first,
                last_name=last,
                gender=random.choice(["male", "female"])
            )
            db.add(person)
            await db.flush()
            
            user = User(
                tenant_id=tenant_id,
                email=f"student{student_num}@demo.edu",
                password_hash=get_password_hash("student123"),
                role=UserRole.student,
                is_active=True
            )
            db.add(user)
            await db.flush()
            
            person.user_id = user.id
            await db.flush()
            
            student = Student(
                tenant_id=tenant_id,
                person_id=person.id,
                student_id=f"STU-2025-{student_num:04d}",
                admission_date=date(2025, 9, 1),
                status=StudentStatus.active,
                father_name=f"{last} Sr.",
                mother_name=f"Mrs. {last}"
            )
            db.add(student)
            await db.flush()
            
            enrollment = Enrollment(
                tenant_id=tenant_id,
                student_id=student.id,
                academic_term_id=term_id,
                grade_level_id=grade.id,
                class_section_id=section.id,
                roll_number=str(i + 1),
                status="active"
            )
            db.add(enrollment)
            
            students.append((student, user))
            student_num += 1
            await db.flush()
    
    return students


async def seed_attendance(db: AsyncSession, tenant_id: int, students: list, sections: list, term_id: int):
    """Create sample attendance records"""
    today = date.today()
    start_date = date(2025, 9, 1)
    
    # Create attendance for last 30 days
    for days_ago in range(30, 0, -1):
        attendance_date = today - timedelta(days=days_ago)
        if attendance_date.weekday() >= 5:  # Skip weekends
            continue
            
        for section, _ in sections:
            for student, _ in students[:3]:  # First 3 students per section
                # 90% present rate
                status = random.choices(
                    [AttendanceStatus.present, AttendanceStatus.absent, AttendanceStatus.late],
                    weights=[85, 10, 5]
                )[0]
                
                attendance = AttendanceRecord(
                    tenant_id=tenant_id,
                    student_id=student.id,
                    class_section_id=section.id,
                    academic_term_id=term_id,
                    date=attendance_date,
                    status=status
                )
                db.add(attendance)
    await db.flush()


async def main():
    """Run all seeds"""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Seeding database...")
    async with async_session() as db:
        # Seed tenant and school
        tenant, school = await seed_tenant(db)
        print(f"Created tenant: {tenant.name}, school: {school.name}")
        
        # Seed academic structure
        term, grades, departments, subjects, sections = await seed_academic_structure(db, school.id)
        print(f"Created academic structure: {len(grades)} grades, {len(subjects)} subjects, {len(sections)} sections")
        
        # Seed grading system
        gs = await seed_grading_system(db, school.id)
        print(f"Created grading system: {gs.name}")
        
        # Seed admin
        admin = await seed_admin_user(db, tenant.id, school.id)
        print(f"Created admin user: {admin.email}")
        
        # Seed teachers
        teachers = await seed_teachers(db, tenant.id, school.id, departments, subjects, term.id)
        print(f"Created {len(teachers)} teachers")
        
        # Seed students
        students = await seed_students(db, tenant.id, school.id, sections, term.id)
        print(f"Created {len(students)} students")
        
        # Seed attendance
        await seed_attendance(db, tenant.id, students, sections, term.id)
        print("Created attendance records")
        
        await db.commit()
    
    print("\n✅ Database seeded successfully!")
    print("\nLogin credentials:")
    print("  Admin: admin@demo.edu / admin123")
    print("  Teacher: john@demo.edu / teacher123")
    print("  Student: student1@demo.edu / student123")


if __name__ == "__main__":
    asyncio.run(main())
