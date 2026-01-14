from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 验证
        if not username or not email or not password:
            flash('所有字段都必须填写', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('两次密码不一致', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('密码至少 6 位', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('邮箱已注册', 'error')
            return render_template('auth/register.html')

        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('用户名或密码错误', 'error')
            return render_template('auth/login.html')

        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=remember)
        flash('登录成功！', 'success')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已登出', 'info')
    return redirect(url_for('index'))
