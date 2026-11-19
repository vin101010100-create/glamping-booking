from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models import ACTIVE_BOOKING_STATUSES, Accommodation, Booking, User
from ..utils import EMAIL_RE, parse_date

booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/profile")
@login_required
def profile():
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("profile.html", bookings=bookings, today=date.today())


@booking_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    phone = (request.form.get("phone") or "").strip()

    errors = []
    if len(name) < 2:
        errors.append("Имя должно содержать минимум 2 символа.")
    if not EMAIL_RE.match(email):
        errors.append("Введите корректный адрес электронной почты.")
    if not errors:
        existing = User.query.filter(
            func.lower(User.email) == email, User.id != current_user.id
        ).first()
        if existing:
            errors.append("Этот адрес электронной почты уже занят другим аккаунтом.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("booking.profile"))

    current_user.name = name
    current_user.email = email
    current_user.phone = phone
    db.session.commit()
    flash("Личные данные обновлены.", "success")
    return redirect(url_for("booking.profile"))


@booking_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    new_password_confirm = request.form.get("new_password_confirm") or ""

    errors = []
    if not current_user.check_password(current_password):
        errors.append("Текущий пароль указан неверно.")
    if len(new_password) < 8:
        errors.append("Новый пароль должен содержать минимум 8 символов.")
    if new_password != new_password_confirm:
        errors.append("Новые пароли не совпадают.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("booking.profile"))

    current_user.set_password(new_password)
    db.session.commit()
    flash("Пароль успешно изменён.", "success")
    return redirect(url_for("booking.profile"))


@booking_bp.route("/accommodation/<int:accommodation_id>/book", methods=["POST"])
@login_required
def create_booking(accommodation_id):
    acc = db.get_or_404(Accommodation, accommodation_id)
    if not acc.is_active:
        flash("Этот объект временно недоступен для бронирования.", "warning")
        return redirect(url_for("main.catalog"))

    check_in_raw = request.form.get("check_in") or ""
    check_out_raw = request.form.get("check_out") or ""
    check_in = parse_date(check_in_raw)
    check_out = parse_date(check_out_raw)

    if not check_in or not check_out:
        flash("Укажите даты заезда и выезда.", "danger")
        return redirect(
            url_for(
                "main.accommodation",
                accommodation_id=acc.id,
                check_in=check_in_raw,
                check_out=check_out_raw,
            )
        )

    today = date.today()
    if check_in < today:
        flash("Дата заезда не может быть в прошлом.", "danger")
        return redirect(url_for("main.accommodation", accommodation_id=acc.id))
    if check_out <= check_in:
        flash("Дата выезда должна быть позже даты заезда.", "danger")
        return redirect(
            url_for(
                "main.accommodation",
                accommodation_id=acc.id,
                check_in=check_in_raw,
                check_out=check_out_raw,
            )
        )
    if (check_out - check_in).days > 60:
        flash("Максимальная длительность бронирования — 60 ночей.", "danger")
        return redirect(
            url_for(
                "main.accommodation",
                accommodation_id=acc.id,
                check_in=check_in_raw,
                check_out=check_out_raw,
            )
        )

    conflict = Booking.query.filter(
        Booking.accommodation_id == acc.id,
        Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        Booking.check_in < check_out,
        Booking.check_out > check_in,
    ).first()
    if conflict:
        flash(
            "Выбранные даты уже заняты. Пожалуйста, выберите другой период.",
            "warning",
        )
        return redirect(url_for("main.accommodation", accommodation_id=acc.id))

    booking = Booking(
        user_id=current_user.id,
        accommodation_id=acc.id,
        check_in=check_in,
        check_out=check_out,
        status="pending",
    )
    db.session.add(booking)
    db.session.commit()

    flash(
        "Бронирование создано. Статус — «Ожидает подтверждения». "
        "Отследить его можно в личном кабинете.",
        "success",
    )
    return redirect(url_for("booking.profile"))


@booking_bp.route("/booking/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    if booking.user_id != current_user.id:
        abort(403)

    if booking.status not in ACTIVE_BOOKING_STATUSES:
        flash("Это бронирование уже нельзя отменить.", "warning")
    elif booking.check_in <= date.today():
        flash("Нельзя отменить бронирование после начала проживания.", "warning")
    else:
        booking.status = "cancelled"
        db.session.commit()
        flash("Бронирование отменено.", "success")

    return redirect(url_for("booking.profile"))
