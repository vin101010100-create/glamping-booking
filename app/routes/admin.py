from datetime import datetime
from functools import wraps
from urllib.parse import urlencode

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..extensions import db
from ..models import (
    ACCOMMODATION_TYPES,
    ACTIVE_BOOKING_STATUSES,
    BOOKING_STATUSES,
    PLACEHOLDER_IMAGE,
    Accommodation,
    Booking,
    User,
)
from ..utils import remove_uploaded_image, save_uploaded_image

admin_bp = Blueprint("admin", __name__)


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "clients": User.query.filter_by(role="client").count(),
        "accommodations": Accommodation.query.count(),
        "active_accommodations": Accommodation.query.filter_by(is_active=True).count(),
        "bookings": Booking.query.count(),
        "pending": Booking.query.filter_by(status="pending").count(),
    }
    recent_bookings = (
        Booking.query.order_by(Booking.created_at.desc()).limit(6).all()
    )
    return render_template(
        "admin/dashboard.html", stats=stats, recent_bookings=recent_bookings
    )


@admin_bp.route("/accommodations")
@admin_required
def accommodations():
    q = (request.args.get("q") or "").strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)

    query = Accommodation.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Accommodation.name.ilike(like),
                Accommodation.location.ilike(like),
            )
        )
    pagination = query.order_by(Accommodation.id.asc()).paginate(
        page=page, per_page=15, error_out=False
    )
    filters = {k: v for k, v in request.args.items() if k != "page" and v}
    return render_template(
        "admin/accommodations.html",
        accommodations=pagination.items,
        pagination=pagination,
        pagination_qs=urlencode(filters),
        q=q,
    )


def _form_data(accommodation=None):
    if request.method == "POST":
        return {
            "name": (request.form.get("name") or "").strip(),
            "type": (request.form.get("type") or "").strip(),
            "location": (request.form.get("location") or "").strip(),
            "price": (request.form.get("price") or "").strip(),
            "capacity": (request.form.get("capacity") or "").strip(),
            "description": (request.form.get("description") or "").strip(),
            "amenities": (request.form.get("amenities") or "").strip(),
            "image": (request.form.get("image") or "").strip(),
            "gallery": (request.form.get("gallery") or "").strip(),
            "is_active": request.form.get("is_active") == "on",
        }
    return {
        "name": accommodation.name if accommodation else "",
        "type": accommodation.type if accommodation else "",
        "location": accommodation.location if accommodation else "",
        "price": accommodation.price if accommodation else "",
        "capacity": accommodation.capacity if accommodation else 2,
        "description": accommodation.description if accommodation else "",
        "amenities": accommodation.amenities if accommodation else "",
        "image": accommodation.image if accommodation else "",
        "gallery": accommodation.gallery if accommodation else "",
        "is_active": accommodation.is_active if accommodation else True,
    }


def _validate_form(data):
    errors = []
    price = None
    capacity = None

    if len(data["name"]) < 3:
        errors.append("Название должно содержать минимум 3 символа.")
    if data["type"] not in ACCOMMODATION_TYPES:
        errors.append("Выберите корректный тип объекта размещения.")
    if len(data["location"]) < 2:
        errors.append("Укажите местоположение объекта.")
    if len(data["description"]) < 20:
        errors.append("Описание должно содержать минимум 20 символов.")

    try:
        price = int(data["price"])
        if price <= 0:
            errors.append("Стоимость должна быть положительным числом.")
    except (TypeError, ValueError):
        errors.append("Укажите корректную стоимость проживания.")

    try:
        capacity = int(data["capacity"])
        if not 1 <= capacity <= 50:
            errors.append("Вместимость должна быть от 1 до 50 гостей.")
    except (TypeError, ValueError):
        errors.append("Укажите корректную вместимость.")

    if len(data["image"]) > 500:
        errors.append("Ссылка на изображение слишком длинная.")

    return errors, price, capacity


def _handle_accommodation_form(accommodation=None):
    data = _form_data(accommodation)

    if request.method == "POST":
        errors, price, capacity = _validate_form(data)
        image_path = data["image"] or (
            accommodation.image if accommodation else PLACEHOLDER_IMAGE
        )

        upload = request.files.get("image_file")
        if not errors and upload and upload.filename:
            saved = save_uploaded_image(upload)
            if saved is None:
                errors.append(
                    "Недопустимый формат изображения. Разрешены: JPG, PNG, WEBP, GIF."
                )
            else:
                image_path = saved

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "admin/accommodation_form.html",
                acc=accommodation,
                data=data,
            )

        old_image = accommodation.image if accommodation else None

        if accommodation is None:
            accommodation = Accommodation()
            db.session.add(accommodation)

        accommodation.name = data["name"]
        accommodation.type = data["type"]
        accommodation.location = data["location"]
        accommodation.price = price
        accommodation.capacity = capacity
        accommodation.description = data["description"]
        accommodation.amenities = data["amenities"]
        accommodation.image = image_path or PLACEHOLDER_IMAGE
        accommodation.gallery = data["gallery"]
        accommodation.is_active = data["is_active"]
        if accommodation.created_at is None:
            accommodation.created_at = datetime.utcnow()

        db.session.commit()

        if old_image and old_image != accommodation.image and old_image not in (
            data["gallery"] or ""
        ):
            remove_uploaded_image(old_image)

        flash("Объект размещения сохранён.", "success")
        return redirect(url_for("admin.accommodations"))

    return render_template(
        "admin/accommodation_form.html",
        acc=accommodation,
        data=data,
    )


@admin_bp.route("/accommodations/new", methods=["GET", "POST"])
@admin_required
def new_accommodation():
    return _handle_accommodation_form()


@admin_bp.route("/accommodations/<int:accommodation_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_accommodation(accommodation_id):
    accommodation = db.get_or_404(Accommodation, accommodation_id)
    return _handle_accommodation_form(accommodation)


@admin_bp.route("/accommodations/<int:accommodation_id>/toggle", methods=["POST"])
@admin_required
def toggle_accommodation(accommodation_id):
    accommodation = db.get_or_404(Accommodation, accommodation_id)
    accommodation.is_active = not accommodation.is_active
    db.session.commit()
    state = "опубликован" if accommodation.is_active else "скрыт из каталога"
    flash(f"Объект «{accommodation.name}» {state}.", "success")
    return redirect(url_for("admin.accommodations"))


@admin_bp.route("/accommodations/<int:accommodation_id>/delete", methods=["POST"])
@admin_required
def delete_accommodation(accommodation_id):
    accommodation = db.get_or_404(Accommodation, accommodation_id)
    has_bookings = (
        Booking.query.filter_by(accommodation_id=accommodation.id).first() is not None
    )

    if has_bookings:
        accommodation.is_active = False
        db.session.commit()
        flash(
            "У объекта есть бронирования, поэтому он скрыт из каталога, "
            "а не удалён. История бронирований сохранена.",
            "warning",
        )
    else:
        image = accommodation.image
        gallery_images = list(accommodation.gallery_list)
        name = accommodation.name
        db.session.delete(accommodation)
        db.session.commit()
        for image_path in set(gallery_images + [image]):
            remove_uploaded_image(image_path)
        flash(f"Объект «{name}» удалён.", "success")

    return redirect(url_for("admin.accommodations"))


@admin_bp.route("/bookings")
@admin_required
def bookings():
    status = (request.args.get("status") or "").strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)

    query = Booking.query
    if status in BOOKING_STATUSES:
        query = query.filter(Booking.status == status)

    pagination = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    filters = {k: v for k, v in request.args.items() if k != "page" and v}
    return render_template(
        "admin/bookings.html",
        bookings=pagination.items,
        pagination=pagination,
        pagination_qs=urlencode(filters),
        current_status=status,
    )


@admin_bp.route("/bookings/<int:booking_id>/status", methods=["POST"])
@admin_required
def update_booking_status(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    new_status = request.form.get("status") or ""

    if new_status not in BOOKING_STATUSES:
        flash("Некорректный статус бронирования.", "danger")
    else:
        conflict = None
        if new_status in ACTIVE_BOOKING_STATUSES:
            conflict = Booking.query.filter(
                Booking.id != booking.id,
                Booking.accommodation_id == booking.accommodation_id,
                Booking.status.in_(ACTIVE_BOOKING_STATUSES),
                Booking.check_in < booking.check_out,
                Booking.check_out > booking.check_in,
            ).first()

        if conflict:
            flash(
                "Нельзя установить этот статус: на выбранные даты уже есть "
                f"активное бронирование №{conflict.id}.",
                "danger",
            )
        else:
            booking.status = new_status
            db.session.commit()
            flash(
                f"Статус бронирования №{booking.id} изменён: "
                f"{BOOKING_STATUSES[new_status]}.",
                "success",
            )

    return_status = request.form.get("return_status") or ""
    if return_status in BOOKING_STATUSES:
        return redirect(url_for("admin.bookings", status=return_status))
    return redirect(url_for("admin.bookings"))


@admin_bp.route("/users")
@admin_required
def users():
    q = (request.args.get("q") or "").strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)

    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(User.name.ilike(like), User.email.ilike(like))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    filters = {k: v for k, v in request.args.items() if k != "page" and v}
    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        pagination_qs=urlencode(filters),
        q=q,
    )
