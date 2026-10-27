from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class Role:
    ADMIN = 'admin'
    SUPERVISOR = 'supervisor'
    STUDENT = 'student'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    matric_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.STUDENT)
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Supervisor assigned to this student (null for non-students / unassigned)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Self-referential: a supervisor has many students
    supervised_students = db.relationship(
        'User',
        backref=db.backref('assigned_supervisor', remote_side=[id]),
        foreign_keys=[supervisor_id],
        lazy='dynamic'
    )

    # Projects this user supervises
    supervised_projects = db.relationship(
        'Project',
        back_populates='supervisor',
        foreign_keys='Project.supervisor_id',
        lazy='dynamic'
    )

    # Project memberships (students on projects)
    memberships = db.relationship(
        'ProjectMember',
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Write-up submissions by this student
    submissions = db.relationship(
        'Submission',
        back_populates='student',
        foreign_keys='Submission.student_id',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Reviews written by this user (supervisor)
    reviews_given = db.relationship(
        'Review',
        back_populates='reviewer',
        foreign_keys='Review.reviewer_id',
        lazy='dynamic'
    )

    notifications = db.relationship(
        'Notification',
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == Role.ADMIN

    def is_supervisor(self):
        return self.role == Role.SUPERVISOR

    def is_student(self):
        return self.role == Role.STUDENT

    def __repr__(self):
        return f'<User {self.full_name} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
