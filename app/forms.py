from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField, TextAreaField,
    SelectField, IntegerField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from app.models import User, Role


class LoginForm(FlaskForm):
    identifier = StringField(
        'Matric Number / Email',
        validators=[DataRequired(), Length(min=5, max=120)]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=8, message='Password must be at least 8 characters')]
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')]
    )
    submit = SubmitField('Update Password')


class UserForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    matric_number = StringField('Matric Number', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[
        (Role.STUDENT, 'Student'),
        (Role.SUPERVISOR, 'Supervisor'),
        (Role.ADMIN, 'Administrator')
    ], validators=[DataRequired()])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save User')

    def validate_matric_number(self, field):
        if field.data:
            data = field.data.strip()
            if not (data.isdigit() and len(data) == 10):
                raise ValidationError('Matric number must be exactly 10 digits (e.g. 2460141001)')
            existing = User.query.filter_by(matric_number=data).first()
            if existing and (not hasattr(self, '_user_id') or existing.id != self._user_id):
                raise ValidationError('This matric number is already registered.')


class AssignSupervisorForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    supervisor_id = SelectField('Supervisor', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign')


class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    code = StringField('Project Code', validators=[Optional(), Length(max=30)])
    academic_session = StringField('Academic Session', validators=[Optional(), Length(max=20)])
    level = SelectField('Level', choices=[
        ('', 'Select Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
        ('MSc', 'MSc'),
        ('PhD', 'PhD')
    ])
    status = SelectField('Status', choices=[
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended')
    ])
    supervisor_id = SelectField('Supervisor', coerce=int, validators=[Optional()])
    student_id = SelectField('Assign Student', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Project')


class SubmissionForm(FlaskForm):
    title = StringField('Submission Title', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description / Notes', validators=[Optional()])
    project_id = SelectField('Related Project (optional)', coerce=int, validators=[Optional()])
    document = FileField(
        'Write-up File (PDF or TXT)',
        validators=[
            FileRequired(message='Please select a file'),
            FileAllowed(['pdf', 'txt'], 'Only PDF and TXT files are allowed')
        ]
    )
    submit = SubmitField('Submit Write-up')


class ReviewForm(FlaskForm):
    comments = TextAreaField('Comments / Feedback', validators=[DataRequired()])
    decision = SelectField('Decision', choices=[
        ('approved', 'Approved'),
        ('revision_required', 'Revision Required'),
        ('rejected', 'Rejected'),
        ('noted', 'Noted (comment only)')
    ], validators=[DataRequired()])
    rating = SelectField('Rating (optional)', choices=[
        ('', 'No rating'),
        ('1', '1 - Poor'),
        ('2', '2 - Fair'),
        ('3', '3 - Good'),
        ('4', '4 - Very Good'),
        ('5', '5 - Excellent')
    ], validators=[Optional()])
    submit = SubmitField('Submit Review')
