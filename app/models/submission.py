from datetime import datetime
from app import db


class Submission(db.Model):
    """Student write-up / document submission (PDF or TXT)."""
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_type = db.Column(db.String(10))  # pdf, txt
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(30), default='pending')
    # pending | under_review | approved | revision_required | rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship('Project', back_populates='submissions')
    student = db.relationship(
        'User',
        back_populates='submissions',
        foreign_keys=[student_id]
    )
    reviews = db.relationship(
        'Review',
        back_populates='submission',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Review.created_at.desc()'
    )

    def status_badge(self):
        mapping = {
            'pending': 'secondary',
            'under_review': 'info',
            'approved': 'success',
            'revision_required': 'warning',
            'rejected': 'danger'
        }
        return mapping.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Submission {self.title} v{self.version}>'


class Review(db.Model):
    """Supervisor review / comment / approval on a submission."""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comments = db.Column(db.Text, nullable=False)
    decision = db.Column(db.String(30), nullable=False)
    # approved | revision_required | rejected | noted
    rating = db.Column(db.Integer)  # optional 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submission = db.relationship('Submission', back_populates='reviews')
    reviewer = db.relationship(
        'User',
        back_populates='reviews_given',
        foreign_keys=[reviewer_id]
    )

    def decision_badge(self):
        mapping = {
            'approved': 'success',
            'revision_required': 'warning',
            'rejected': 'danger',
            'noted': 'info'
        }
        return mapping.get(self.decision, 'secondary')

    def __repr__(self):
        return f'<Review {self.decision} on submission {self.submission_id}>'
