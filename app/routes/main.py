from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Notification

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    if current_user.is_supervisor():
        return redirect(url_for('supervisor.dashboard'))
    return redirect(url_for('student.dashboard'))


@main_bp.route('/notifications')
@login_required
def notifications():
    notes = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    for n in notes:
        if not n.is_read:
            n.is_read = True
    db.session.commit()
    return render_template(
        'shared/notifications.html', notifications=notes, title='Notifications'
    )


@main_bp.route('/profile')
@login_required
def profile():
    return render_template('shared/profile.html', title='My Profile')
