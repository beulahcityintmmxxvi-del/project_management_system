from datetime import datetime
from app import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(30), unique=True, index=True)
    status = db.Column(db.String(30), default='ongoing')
    academic_session = db.Column(db.String(20))
    level = db.Column(db.String(10))
    progress_percentage = db.Column(db.Float, default=0.0)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    start_date = db.Column(db.Date)
    expected_end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supervisor = db.relationship(
        'User',
        back_populates='supervised_projects',
        foreign_keys=[supervisor_id]
    )
    members = db.relationship(
        'ProjectMember',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    submissions = db.relationship(
        'Submission',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    milestones = db.relationship(
        'Milestone',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Milestone.due_date'
    )

    def get_status_badge(self):
        badges = {
            'proposed': 'secondary',
            'approved': 'info',
            'ongoing': 'primary',
            'completed': 'success',
            'suspended': 'danger'
        }
        return badges.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Project {self.code}: {self.title}>'


class ProjectMember(db.Model):
    __tablename__ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_in_project = db.Column(db.String(50), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', back_populates='members')
    user = db.relationship('User', back_populates='memberships')

    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )


class Milestone(db.Model):
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', back_populates='milestones')
