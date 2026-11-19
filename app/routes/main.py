from datetime import date
from urllib.parse import urlencode

from flask import Blueprint, abort, current_app, render_template, request
from flask_login import current_user
from sqlalchemy import func, or_

from ..extensions import db
from ..models import ACCOMMODATION_TYPES, ACTIVE_BOOKING_STATUSES, Accommodation, Booking
from ..utils import parse_date

main_bp = Blueprint("main", __name__)


def _locations() -> list[str]:
    rows = (
        db.session.query(Accommodation.location)
        .filter(Accommodation.is_active.is_(True))
        .distinct()
        .order_by(Accommodation.location)
        .all()
    )
    return [row[0] for row in rows if row[0]]


@main_bp.route("/")
def index():
    popular = (
        db.session.query(Accommodation)
        .outerjoin(Booking, Booking.accommodation_id == Accommodation.id)
        .filter(Accommodation.is_active.is_(True))
        .group_by(Accommodation.id)
        .order_by(func.count(Booking.id).desc(), Accommodation.id.asc())
        .limit(3)
        .all()
    )
    stats = {
        "accommodations": Accommodation.query.filter_by(is_active=True).count(),
        "locations": len(_locations()),
        "bookings": Booking.query.count(),
    }
    return render_template(
        "index.html",
        popular=popular,
        locations=_locations(),
        stats=stats,
        today=date.today(),
    )


@main_bp.route("/catalog")
def catalog():
    q = (request.args.get("q") or "").strip()
    location = (request.args.get("location") or "").strip()
    accommodation_type = (request.args.get("type") or "").strip()
    sort = (request.args.get("sort") or "recommended").strip()
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    check_in_raw = request.args.get("check_in") or ""
    check_out_raw = request.args.get("check_out") or ""
    check_in = parse_date(check_in_raw)
    check_out = parse_date(check_out_raw)
    page = max(request.args.get("page", 1, type=int) or 1, 1)

    date_error = None
    if (check_in_raw or check_out_raw) and not (
        check_in and check_out and check_out > check_in
    ):
        date_error = "Укажите корректный период: дата выезда должна быть позже даты заезда."
        check_in = check_out = None
    elif check_in and check_in < date.today():
        date_error = "Дата заезда не может быть в прошлом."
        check_in = check_out = None

    query = Accommodation.query.filter(Accommodation.is_active.is_(True))

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Accommodation.name.ilike(like),
                Accommodation.description.ilike(like),
                Accommodation.location.ilike(like),
            )
        )
    if location:
        query = query.filter(Accommodation.location == location)
    if accommodation_type in ACCOMMODATION_TYPES:
        query = query.filter(Accommodation.type == accommodation_type)
    if min_price is not None:
        query = query.filter(Accommodation.price >= min_price)
    if max_price is not None:
        query = query.filter(Accommodation.price <= max_price)

    if check_in and check_out:
        conflicting = db.session.query(Booking.accommodation_id).filter(
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        )
        query = query.filter(~Accommodation.id.in_(conflicting))

    if sort == "price_asc":
        query = query.order_by(Accommodation.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Accommodation.price.desc())
    elif sort == "new":
        query = query.order_by(Accommodation.created_at.desc())
    else:
        query = query.order_by(Accommodation.id.asc())

    pagination = query.paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )

    filters = {
        key: value
        for key, value in request.args.items()
        if key != "page" and value
    }
    pagination_qs = urlencode(filters)

    return render_template(
        "catalog.html",
        accommodations=pagination.items,
        pagination=pagination,
        pagination_qs=pagination_qs,
        locations=_locations(),
        date_error=date_error,
        today=date.today(),
    )


@main_bp.route("/accommodation/<int:accommodation_id>")
def accommodation(accommodation_id):
    accommodation_obj = db.get_or_404(Accommodation, accommodation_id)
    if not accommodation_obj.is_active and not (
        current_user.is_authenticated and current_user.is_admin
    ):
        abort(404)

    related = (
        Accommodation.query.filter(
            Accommodation.is_active.is_(True),
            Accommodation.id != accommodation_obj.id,
            Accommodation.type == accommodation_obj.type,
        )
        .limit(3)
        .all()
    )
    if len(related) < 3:
        existing_ids = [item.id for item in related] + [accommodation_obj.id]
        extra = (
            Accommodation.query.filter(
                Accommodation.is_active.is_(True),
                ~Accommodation.id.in_(existing_ids),
            )
            .limit(3 - len(related))
            .all()
        )
        related.extend(extra)

    return render_template(
        "accommodation.html",
        acc=accommodation_obj,
        related=related,
        today=date.today(),
    )
