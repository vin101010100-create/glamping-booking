from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import func

from ..extensions import db
from ..models import User
from ..utils import EMAIL_RE, is_safe_url

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    name = ""
    email = ""

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm") or ""

        errors = []
        if len(name) < 2:
            errors.append("Имя должно содержать минимум 2 символа.")
        if not EMAIL_RE.match(email):
            errors.append("Введите корректный адрес электронной почты.")
        if len(password) < 8:
            errors.append("Пароль должен содержать минимум 8 символов.")
        if password != password_confirm:
            errors.append("Пароли не совпадают.")
        if not errors:
            existing = User.query.filter(func.lower(User.email) == email).first()
            if existing:
                errors.append("Аккаунт с такой электронной почтой уже существует.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", name=name, email=email)

        user = User(name=name, email=email, role="client")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Аккаунт создан. Теперь вы можете войти в систему.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", name=name, email=email)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    email = ""

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "on"

        user = User.query.filter(func.lower(User.email) == email).first()
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Добро пожаловать, {user.name}!", "success")
            next_page = request.args.get("next")
            if is_safe_url(next_page):
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("main.index"))

        flash("Неверная электронная почта или пароль.", "danger")

    return render_template("login.html", email=email)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("main.index"))
