import os
from datetime import datetime

import click
from flask import Flask, render_template

from config import Config

from .extensions import csrf, db, login_manager, migrate
from .models import ACCOMMODATION_TYPES, BOOKING_STATUSES, User


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Для доступа к этой странице необходимо войти в систему."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.booking import booking_bp
    from .routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    _register_cli(app)
    _register_template_helpers(app)
    _register_error_handlers(app)
    _register_security_headers(app)

    return app


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def _register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Создать таблицы базы данных без миграций."""
        db.create_all()
        click.echo("Таблицы базы данных созданы.")

    @app.cli.command("seed-db")
    def seed_db():
        """Заполнить базу демонстрационными данными."""
        db.create_all()
        from .seed import seed_database

        seed_database()


def _register_template_helpers(app):
    @app.context_processor
    def inject_globals():
        return {
            "BOOKING_STATUSES": BOOKING_STATUSES,
            "ACCOMMODATION_TYPES": ACCOMMODATION_TYPES,
            "current_year": datetime.now().year,
        }

    @app.template_filter("rub")
    def format_rub(value):
        if value is None:
            return "—"
        try:
            return f"{int(value):,}".replace(",", " ") + " ₽"
        except (TypeError, ValueError):
            return value

    @app.template_filter("date_ru")
    def format_date_ru(value):
        if not value:
            return "—"
        months = (
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
        )
        return f"{value.day} {months[value.month - 1]} {value.year}"

    @app.template_filter("plural_ru")
    def plural_ru(value, one, few, many):
        try:
            number = abs(int(value))
        except (TypeError, ValueError):
            return many
        if 11 <= number % 100 <= 14:
            return many
        last = number % 10
        if last == 1:
            return one
        if 2 <= last <= 4:
            return few
        return many


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_security_headers(app):
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response
