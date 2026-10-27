from functools import wraps
import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Role, Project, ProjectMember, Submission, Review
from app.forms import UserForm, AssignSupervisorForm, ProjectForm

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Administrator access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_students': User.query.filter_by(role=Role.STUDENT).count(),
        'total_supervisors': User.query.filter_by(role=Role.SUPERVISOR).count(),
        'total_projects': Project.query.count(),
        'pending_submissions': Submission.query.filter_by(status='pending').count(),
        'unassigned_students': User.query.filter_by(
            role=Role.STUDENT, supervisor_id=None
        ).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_users=recent_users,
        title='Admin Dashboard'
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    q = request.args.get('q', '').strip()

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
                User.matric_number.ilike(like)
            )
        )
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        'admin/users.html',
        pagination=pagination,
        role_filter=role_filter,
        q=q,
        title='Manage Users'
    )


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.strip().lower(),
            matric_number=form.matric_number.data.strip() if form.matric_number.data else None,
            role=form.role.data,
            department=form.department.data,
            phone=form.phone.data,
            is_active=form.is_active.data,
            must_change_password=True
        )
        if form.role.data == Role.STUDENT:
            pwd = form.password.data or 'Student@123'
        else:
            pwd = form.password.data or secrets.token_urlsafe(10)
        user.set_password(pwd)
        db.session.add(user)
        db.session.commit()
        flash(f'User created. Temporary password: {pwd}', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, title='Create User')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form._user_id = user.id
    if form.validate_on_submit():
        user.full_name = form.full_name.data.strip()
        user.email = form.email.data.strip().lower()
        user.matric_number = (
            form.matric_number.data.strip() if form.matric_number.data else None
        )
        user.role = form.role.data
        user.department = form.department.data
        user.phone = form.phone.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
            user.must_change_password = True
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.users'))
    return render_template(
        'admin/user_form.html', form=form, user=user, title='Edit User'
    )


@admin_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@admin_required
def assignments():
    """Assign students to supervisors for supervision."""
    form = AssignSupervisorForm()
    form.student_id.choices = [(0, '— Select Student —')] + [
        (u.id, f'{u.full_name} ({u.matric_number or u.email})')
        for u in User.query.filter_by(role=Role.STUDENT, is_active=True)
        .order_by(User.full_name).all()
    ]
    form.supervisor_id.choices = [(0, '— Select Supervisor —')] + [
        (u.id, f'{u.full_name} ({u.department or "—"})')
        for u in User.query.filter_by(role=Role.SUPERVISOR, is_active=True)
        .order_by(User.full_name).all()
    ]

    if form.validate_on_submit():
        student = User.query.get(form.student_id.data)
        supervisor = User.query.get(form.supervisor_id.data)
        if not student or not student.is_student():
            flash('Invalid student selected.', 'danger')
        elif not supervisor or not supervisor.is_supervisor():
            flash('Invalid supervisor selected.', 'danger')
        else:
            student.supervisor_id = supervisor.id
            db.session.commit()
            flash(
                f'{student.full_name} has been assigned to {supervisor.full_name}.',
                'success'
            )
            return redirect(url_for('admin.assignments'))

    # Current assignments list
    assigned = (
        User.query
        .filter(User.role == Role.STUDENT, User.supervisor_id.isnot(None))
        .order_by(User.full_name)
        .all()
    )
    unassigned = (
        User.query
        .filter_by(role=Role.STUDENT, supervisor_id=None)
        .order_by(User.full_name)
        .all()
    )
    return render_template(
        'admin/assignments.html',
        form=form,
        assigned=assigned,
        unassigned=unassigned,
        title='Assign Students to Supervisors'
    )


@admin_bp.route('/assignments/<int:student_id>/unassign', methods=['POST'])
@login_required
@admin_required
def unassign_student(student_id):
    student = User.query.get_or_404(student_id)
    if student.is_student():
        student.supervisor_id = None
        db.session.commit()
        flash(f'{student.full_name} has been unassigned.', 'info')
    return redirect(url_for('admin.assignments'))


@admin_bp.route('/projects')
@login_required
@admin_required
def projects():
    page = request.args.get('page', 1, type=int)
    pagination = (
        Project.query.order_by(Project.created_at.desc())
        .paginate(page=page, per_page=15, error_out=False)
    )
    return render_template(
        'admin/projects.html', pagination=pagination, title='Manage Projects'
    )


@admin_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_project():
    form = ProjectForm()
    form.supervisor_id.choices = [(0, '— Select Supervisor —')] + [
        (u.id, u.full_name)
        for u in User.query.filter_by(role=Role.SUPERVISOR, is_active=True).all()
    ]
    form.student_id.choices = [(0, '— Select Student —')] + [
        (u.id, f'{u.full_name} ({u.matric_number or ""})')
        for u in User.query.filter_by(role=Role.STUDENT, is_active=True).all()
    ]
    if form.validate_on_submit():
        code = form.code.data.strip() if form.code.data else f'PRJ-{secrets.token_hex(3).upper()}'
        project = Project(
            title=form.title.data.strip(),
            description=form.description.data,
            code=code,
            academic_session=form.academic_session.data,
            level=form.level.data,
            status=form.status.data or 'ongoing',
            supervisor_id=form.supervisor_id.data or None,
            created_by=current_user.id
        )
        db.session.add(project)
        db.session.flush()

        if form.student_id.data:
            member = ProjectMember(
                project_id=project.id,
                user_id=form.student_id.data,
                role_in_project='leader'
            )
            db.session.add(member)
            # Also link student to supervisor if supervisor set
            if form.supervisor_id.data:
                student = User.query.get(form.student_id.data)
                if student and not student.supervisor_id:
                    student.supervisor_id = form.supervisor_id.data

        db.session.commit()
        flash('Project created successfully.', 'success')
        return redirect(url_for('admin.projects'))
    return render_template(
        'admin/project_form.html', form=form, title='Create Project'
    )


@admin_bp.route('/submissions')
@login_required
@admin_required
def submissions():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Submission.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(Submission.submitted_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        'admin/submissions.html',
        pagination=pagination,
        status=status,
        title='All Submissions'
    )
