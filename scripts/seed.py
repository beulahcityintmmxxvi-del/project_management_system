#!/usr/bin/env python3
"""Seed admin, supervisors, students, assignments, and a sample project."""
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Role, Project, ProjectMember

app = create_app()

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@psms.local')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@2024Secure')
DEFAULT_STUDENT_PASSWORD = 'Student@123'
DEFAULT_SUPERVISOR_PASSWORD = 'Supervisor@123'


def seed():
    with app.app_context():
        # Drop and recreate for clean seed when using SQLite (safe for dev)
        db.create_all()

        # Admin
        admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=ADMIN_EMAIL,
                full_name='System Administrator',
                role=Role.ADMIN,
                department='ICT Directorate',
                must_change_password=False,
                is_active=True
            )
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            print(f'[+] Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}')
        else:
            print(f'[=] Admin exists: {ADMIN_EMAIL}')

        # Supervisors
        supervisors_data = [
            ('Dr. Adebayo Okonkwo', 'adebayo.okonkwo@university.edu', 'Computer Science'),
            ('Prof. Chioma Eze', 'chioma.eze@university.edu', 'Software Engineering'),
            ('Dr. Ibrahim Musa', 'ibrahim.musa@university.edu', 'Information Systems'),
        ]
        supervisors = []
        for name, email, dept in supervisors_data:
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(
                    email=email,
                    full_name=name,
                    role=Role.SUPERVISOR,
                    department=dept,
                    must_change_password=False,
                    is_active=True
                )
                u.set_password(DEFAULT_SUPERVISOR_PASSWORD)
                db.session.add(u)
                print(f'[+] Supervisor: {email}')
            supervisors.append(u)

        db.session.flush()

        # Students (assigned to supervisors)
        students_data = [
            ('2460141001', 'Adaobi Nwosu', 'adaobi.nwosu@student.edu', 'Computer Science', 0),
            ('2460141002', 'Chinedu Okafor', 'chinedu.okafor@student.edu', 'Computer Science', 0),
            ('2460141003', 'Fatima Bello', 'fatima.bello@student.edu', 'Software Engineering', 1),
            ('2460141004', 'Emeka Obi', 'emeka.obi@student.edu', 'Information Systems', 2),
            ('2460141005', 'Aisha Mohammed', 'aisha.mohammed@student.edu', 'Computer Science', 0),
            ('2460141006', 'Tunde Adeyemi', 'tunde.adeyemi@student.edu', 'Software Engineering', 1),
        ]
        students = []
        for matric, name, email, dept, sup_idx in students_data:
            u = User.query.filter_by(matric_number=matric).first()
            if not u:
                u = User(
                    matric_number=matric,
                    email=email,
                    full_name=name,
                    role=Role.STUDENT,
                    department=dept,
                    supervisor_id=supervisors[sup_idx].id,
                    must_change_password=True,
                    is_active=True
                )
                u.set_password(DEFAULT_STUDENT_PASSWORD)
                db.session.add(u)
                print(f'[+] Student: {matric} → {supervisors[sup_idx].full_name}')
            students.append(u)

        db.session.flush()

        # Sample project
        if not Project.query.filter_by(code='CSC-2024-001').first():
            project = Project(
                title='Intelligent Campus Navigation System using Computer Vision',
                code='CSC-2024-001',
                description='Mobile app using computer vision for campus navigation.',
                status='ongoing',
                progress_percentage=40.0,
                academic_session='2024/2025',
                level='400',
                supervisor_id=supervisors[0].id,
                created_by=admin.id,
                start_date=date.today() - timedelta(days=45),
                expected_end_date=date.today() + timedelta(days=120)
            )
            db.session.add(project)
            db.session.flush()
            for st in students[:2]:
                db.session.add(ProjectMember(
                    project_id=project.id,
                    user_id=st.id,
                    role_in_project='leader' if st == students[0] else 'member'
                ))
            print('[+] Project: CSC-2024-001')

        db.session.commit()

        print('\n========== SEED COMPLETE ==========')
        print(f'Admin      : {ADMIN_EMAIL} / {ADMIN_PASSWORD}')
        print(f'Student    : 2460141001 / {DEFAULT_STUDENT_PASSWORD}')
        print(f'Supervisor : adebayo.okonkwo@university.edu / {DEFAULT_SUPERVISOR_PASSWORD}')
        print('===================================')


if __name__ == '__main__':
    seed()
