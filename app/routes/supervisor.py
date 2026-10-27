from functools import wraps
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, send_from_directory, abort
)
from flask_login import login_required, current_user
from app import db
from app.models import (
    User, Role, Project, Submission, Review, Notification
)
from app.forms import ReviewForm

supervisor_bp = Blueprint('supervisor', __name__)


def supervisor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not (
            current_user.is_supervisor() or current_user.is_admin()
        ):
            flash('Supervisor access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@supervisor_bp.route('/dashboard')
@login_required
@supervisor_required
def dashboard():
    students = (
        User.query
        .filter_by(role=Role.STUDENT, supervisor_id=current_user.id)
        .order_by(User.full_name)
        .all()
    )
    student_ids = [s.id for s in students]
    pending = []
    if student_ids:
        pending = (
            Submission.query
            .filter(
                Submission.student_id.in_(student_ids),
                Submission.status.in_(['pending', 'under_review'])
            )
            .order_by(Submission.submitted_at.desc())
            .limit(10)
            .all()
        )
    projects = Project.query.filter_by(supervisor_id=current_user.id).all()
    stats = {
        'students': len(students),
        'projects': len(projects),
        'pending_reviews': len(pending),
        'approved': Submission.query.filter(
            Submission.student_id.in_(student_ids) if student_ids else False,
            Submission.status == 'approved'
        ).count() if student_ids else 0
    }
    return render_template(
        'supervisor/dashboard.html',
        students=students,
        pending=pending,
        projects=projects,
        stats=stats,
        title='Supervisor Dashboard'
    )


@supervisor_bp.route('/students')
@login_required
@supervisor_required
def students():
    """List all students assigned to this supervisor by admin."""
    students = (
        User.query
        .filter_by(role=Role.STUDENT, supervisor_id=current_user.id)
        .order_by(User.full_name)
        .all()
    )
    # Attach submission counts
    data = []
    for s in students:
        total = Submission.query.filter_by(student_id=s.id).count()
        pending = Submission.query.filter_by(
            student_id=s.id, status='pending'
        ).count()
        approved = Submission.query.filter_by(
            student_id=s.id, status='approved'
        ).count()
        data.append({
            'user': s,
            'total': total,
            'pending': pending,
            'approved': approved
        })
    return render_template(
        'supervisor/students.html',
        students=data,
        title='My Students'
    )


@supervisor_bp.route('/students/<int:student_id>')
@login_required
@supervisor_required
def student_detail(student_id):
    student = User.query.get_or_404(student_id)
    if student.supervisor_id != current_user.id and not current_user.is_admin():
        abort(403)
    submissions = (
        Submission.query
        .filter_by(student_id=student.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    return render_template(
        'supervisor/student_detail.html',
        student=student,
        submissions=submissions,
        title=student.full_name
    )


@supervisor_bp.route('/submissions')
@login_required
@supervisor_required
def submissions():
    students = User.query.filter_by(
        role=Role.STUDENT, supervisor_id=current_user.id
    ).all()
    student_ids = [s.id for s in students]
    status = request.args.get('status', '')

    if not student_ids:
        items = []
    else:
        query = Submission.query.filter(Submission.student_id.in_(student_ids))
        if status:
            query = query.filter_by(status=status)
        items = query.order_by(Submission.submitted_at.desc()).all()

    return render_template(
        'supervisor/submissions.html',
        submissions=items,
        status=status,
        title='Student Submissions'
    )


@supervisor_bp.route('/submissions/<int:submission_id>', methods=['GET', 'POST'])
@login_required
@supervisor_required
def submission_detail(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    student = submission.student

    # Access control: must be assigned supervisor (or admin)
    if student.supervisor_id != current_user.id and not current_user.is_admin():
        abort(403)

    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            submission_id=submission.id,
            reviewer_id=current_user.id,
            comments=form.comments.data.strip(),
            decision=form.decision.data,
            rating=int(form.rating.data) if form.rating.data else None
        )
        db.session.add(review)

        # Update submission status based on decision
        if form.decision.data == 'approved':
            submission.status = 'approved'
        elif form.decision.data == 'revision_required':
            submission.status = 'revision_required'
        elif form.decision.data == 'rejected':
            submission.status = 'rejected'
        else:
            submission.status = 'under_review'

        # Notify student
        notif = Notification(
            user_id=student.id,
            title='Review Received',
            message=(
                f'Your submission "{submission.title}" was reviewed: '
                f'{form.decision.data.replace("_", " ").title()}.'
            ),
            link=url_for('student.submission_detail', submission_id=submission.id),
            notification_type='success' if form.decision.data == 'approved' else 'info'
        )
        db.session.add(notif)
        db.session.commit()
        flash('Review submitted successfully.', 'success')
        return redirect(url_for(
            'supervisor.submission_detail', submission_id=submission.id
        ))

    reviews = submission.reviews.order_by(Review.created_at.desc()).all()
    return render_template(
        'supervisor/submission_detail.html',
        submission=submission,
        student=student,
        form=form,
        reviews=reviews,
        title=submission.title
    )


@supervisor_bp.route('/submissions/<int:submission_id>/download')
@login_required
@supervisor_required
def download_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    student = submission.student
    if student.supervisor_id != current_user.id and not current_user.is_admin():
        abort(403)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        submission.filename,
        as_attachment=True,
        download_name=submission.original_filename or submission.filename
    )


@supervisor_bp.route('/projects')
@login_required
@supervisor_required
def projects():
    projects = (
        Project.query
        .filter_by(supervisor_id=current_user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return render_template(
        'supervisor/projects.html', projects=projects, title='My Projects'
    )
