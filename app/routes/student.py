from functools import wraps
import os
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, send_from_directory, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import (
    User, Project, ProjectMember, Submission, Review, Notification, Role
)
from app.forms import SubmissionForm

student_bp = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student():
            flash('Student access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
    projects = [m.project for m in memberships]
    submissions = (
        Submission.query
        .filter_by(student_id=current_user.id)
        .order_by(Submission.submitted_at.desc())
        .limit(5)
        .all()
    )
    supervisor = current_user.assigned_supervisor
    pending = Submission.query.filter_by(
        student_id=current_user.id, status='pending'
    ).count()
    approved = Submission.query.filter_by(
        student_id=current_user.id, status='approved'
    ).count()
    return render_template(
        'student/dashboard.html',
        projects=projects,
        submissions=submissions,
        supervisor=supervisor,
        pending=pending,
        approved=approved,
        title='Student Dashboard'
    )


@student_bp.route('/projects')
@login_required
@student_required
def projects():
    memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
    projects = [m.project for m in memberships]
    return render_template(
        'student/projects.html', projects=projects, title='My Projects'
    )


@student_bp.route('/submissions')
@login_required
@student_required
def submissions():
    items = (
        Submission.query
        .filter_by(student_id=current_user.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    return render_template(
        'student/submissions.html', submissions=items, title='My Submissions'
    )


@student_bp.route('/submissions/new', methods=['GET', 'POST'])
@login_required
@student_required
def submit_writeup():
    form = SubmissionForm()
    memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
    form.project_id.choices = [(0, '— No project / General —')] + [
        (m.project.id, m.project.title) for m in memberships
    ]

    if form.validate_on_submit():
        file = form.document.data
        original = secure_filename(file.filename)
        ext = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
        if ext not in ('pdf', 'txt'):
            flash('Only PDF and TXT files are allowed.', 'danger')
            return render_template(
                'student/submission_form.html', form=form, title='Submit Write-up'
            )

        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        matric = current_user.matric_number or f'user{current_user.id}'
        stored_name = f'{matric}_{timestamp}.{ext}'
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, stored_name))

        project_id = form.project_id.data if form.project_id.data else None

        # Version: count existing with same title for this student
        existing_count = Submission.query.filter_by(
            student_id=current_user.id, title=form.title.data.strip()
        ).count()

        submission = Submission(
            project_id=project_id,
            student_id=current_user.id,
            title=form.title.data.strip(),
            description=form.description.data,
            filename=stored_name,
            original_filename=original,
            file_type=ext,
            version=existing_count + 1,
            status='pending'
        )
        db.session.add(submission)

        # Notify assigned supervisor
        if current_user.supervisor_id:
            notif = Notification(
                user_id=current_user.supervisor_id,
                title='New Write-up Submission',
                message=(
                    f'{current_user.full_name} submitted "{submission.title}" '
                    f'for review.'
                ),
                link=url_for('supervisor.submission_detail', submission_id=0),
                notification_type='info'
            )
            db.session.add(notif)
            db.session.flush()
            notif.link = url_for(
                'supervisor.submission_detail', submission_id=submission.id
            )

        db.session.commit()
        flash('Write-up submitted successfully. Awaiting supervisor review.', 'success')
        return redirect(url_for('student.submissions'))

    return render_template(
        'student/submission_form.html', form=form, title='Submit Write-up'
    )


@student_bp.route('/submissions/<int:submission_id>')
@login_required
@student_required
def submission_detail(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id:
        abort(403)
    reviews = submission.reviews.order_by(Review.created_at.desc()).all()
    return render_template(
        'student/submission_detail.html',
        submission=submission,
        reviews=reviews,
        title=submission.title
    )


@student_bp.route('/submissions/<int:submission_id>/download')
@login_required
@student_required
def download_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id:
        abort(403)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        submission.filename,
        as_attachment=True,
        download_name=submission.original_filename or submission.filename
    )
