from datetime import date, datetime

from flask import url_for
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

BOOKING_STATUSES = {
    "pending": "Ожидает подтверждения",
    "confirmed": "Подтверждено",
    "cancelled": "Отменено",
    "completed": "Завершено",
}
ACTIVE_BOOKING_STATUSES = ("pending", "confirmed")

ACCOMMODATION_TYPES = (
    "Глэмпинг",
    "База отдыха",
    "Эко-отель",
    "Кемпинг",
    "Усадьба",
)

ROLE_LABELS = {
    "client": "Клиент",
    "admin": "Администратор",
}

PLACEHOLDER_IMAGE = "images/placeholder.svg"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    bookings = db.relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Booking.created_at.desc()",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"


class Accommodation(db.Model):
    __tablename__ = "accommodations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    amenities = db.Column(db.Text)
    image = db.Column(db.String(500))
    gallery = db.Column(db.Text)
    capacity = db.Column(db.Integer, nullable=False, default=2)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    bookings = db.relationship("Booking", back_populates="accommodation")

    @property
    def amenities_list(self) -> list[str]:
        if not self.amenities:
            return []
        raw = self.amenities.replace("\n", ",")
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def gallery_list(self) -> list[str]:
        items: list[str] = []
        if self.gallery:
            raw = self.gallery.replace(",", "\n")
            items = [line.strip() for line in raw.splitlines() if line.strip()]
        cover = self.image or PLACEHOLDER_IMAGE
        if not items:
            return [cover]
        if cover not in items:
            items.insert(0, cover)
        return items

    @staticmethod
    def media_url(path: str | None) -> str:
        if not path:
            path = PLACEHOLDER_IMAGE
        if path.startswith(("http://", "https://", "//")):
            return path
        if path.startswith("/"):
            return path
        return url_for("static", filename=path)

    @property
    def cover_url(self) -> str:
        return self.media_url(self.image)

    @property
    def gallery_urls(self) -> list[str]:
        return [self.media_url(path) for path in self.gallery_list]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Accommodation {self.name}>"


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    accommodation_id = db.Column(
        db.Integer, db.ForeignKey("accommodations.id"), nullable=False, index=True
    )
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="bookings")
    accommodation = db.relationship("Accommodation", back_populates="bookings")

    @property
    def nights(self) -> int:
        return max((self.check_out - self.check_in).days, 0)

    @property
    def total_price(self) -> int:
        if not self.accommodation:
            return 0
        return self.nights * self.accommodation.price

    @property
    def status_label(self) -> str:
        return BOOKING_STATUSES.get(self.status, self.status)

    @property
    def is_cancellable(self) -> bool:
        return (
            self.status in ACTIVE_BOOKING_STATUSES
            and self.check_in > date.today()
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Booking {self.id} {self.check_in}—{self.check_out}>"
