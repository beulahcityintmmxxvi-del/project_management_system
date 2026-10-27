from datetime import datetime
from app import db


class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    predicted_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    features_used = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', backref='predictions')
    student = db.relationship('User', backref='predictions')
