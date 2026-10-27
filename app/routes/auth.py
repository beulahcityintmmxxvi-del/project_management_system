from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import LoginForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        password = form.password.data

        user = None
        if identifier.isdigit() and len(identifier) == 10:
            user = User.query.filter_by(matric_number=identifier).first()
        else:
            user = User.query.filter_by(email=identifier.lower()).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            if user.must_change_password:
                flash('Please change your default password for security.', 'warning')
                return redirect(url_for('auth.change_password'))

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))

        flash('Invalid credentials or inactive account.', 'danger')

    return render_template('auth/login.html', form=form, title='Login')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template(
                'auth/change_password.html', form=form, title='Change Password'
            )

        current_user.set_password(form.new_password.data)
        current_user.must_change_password = False
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template(
        'auth/change_password.html', form=form, title='Change Password'
    )
