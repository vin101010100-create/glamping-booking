from datetime import date, datetime, timedelta

from .extensions import db
from .models import Accommodation, Booking, User

ADMIN_EMAIL = "admin@glamping.ru"
ADMIN_PASSWORD = "admin12345"
CLIENT_EMAIL = "client@example.com"
CLIENT_PASSWORD = "client12345"

ACCOMMODATIONS = [
    {
        "name": "Глэмпинг «Ленские столбы»",
        "description": (
            "Уединённые купольные домики у подножия знаменитых Ленских столбов. "
            "Из панорамных окон открывается вид на реку Лену и скалы, а вечером — "
            "на звёздное небо. Идеальный вариант для романтических выходных и фототура."
        ),
        "location": "Хангаласский улус, Ленские столбы",
        "price": 8500,
        "type": "Глэмпинг",
        "amenities": "Панорамные окна, Тёплый пол, Завтрак, Баня, Wi-Fi, Трансфер",
        "image": "images/acc-1.svg",
        "gallery": "images/acc-1.svg\nimages/gallery-1.svg\nimages/gallery-2.svg",
        "capacity": 2,
    },
    {
        "name": "База отдыха «Булуус»",
        "description": (
            "Семейная база отдыха рядом с легендарными незамерзающими источниками Булуус. "
            "Деревянные домики, просторная общая кухня и чистая родниковая вода. "
            "Подходит для отдыха с детьми и небольших дружных компаний."
        ),
        "location": "Хангаласский улус, озеро Булуус",
        "price": 6200,
        "type": "База отдыха",
        "amenities": "Мангал, Тёплая кухня, Детская площадка, Парковка, Прокат лодок, Баня",
        "image": "images/acc-2.svg",
        "gallery": "images/acc-2.svg\nimages/gallery-2.svg",
        "capacity": 4,
    },
    {
        "name": "Эко-отель «Табага»",
        "description": (
            "Современный эко-отель в сосновом бору в двадцати минутах от Якутска. "
            "Номера отделаны натуральными материалами, в ресторане подают блюда локальной "
            "кухни, а из сауны открывается вид на лес. Удобная база для знакомства с городом."
        ),
        "location": "Якутск, Табага",
        "price": 5200,
        "type": "Эко-отель",
        "amenities": "Завтрак, Сауна, Wi-Fi, Парковка, Прокат велосипедов, Ресторан",
        "image": "images/acc-3.svg",
        "gallery": "images/acc-3.svg\nimages/gallery-1.svg",
        "capacity": 3,
    },
    {
        "name": "Глэмпинг «Оймякон»",
        "description": (
            "Экспедиционный глэмпинг в самом холодном обитаемом месте планеты. "
            "Тёплые модульные домики с автономным отоплением, полярное сияние прямо над "
            "палаткой и авторские туры к озеру Лабынкыр. Для тех, кто ищет приключение."
        ),
        "location": "Оймяконский улус, Оймякон",
        "price": 12500,
        "type": "Глэмпинг",
        "amenities": "Автономное отопление, Северное сияние, Завтрак, Трансфер, Тёплый санузел, Гид",
        "image": "images/acc-4.svg",
        "gallery": "images/acc-4.svg\nimages/gallery-3.svg",
        "capacity": 2,
    },
    {
        "name": "Кемпинг «Синские столбы»",
        "description": (
            "Палаточный лагерь у подножия Синских столбов — одного из самых впечатляющих "
            "природных памятников Якутии. Организованные сплавы, походы и вечерние истории "
            "у костра. Всё необходимое снаряжение предоставляется."
        ),
        "location": "Верхоянский район, река Синяя",
        "price": 4800,
        "type": "Кемпинг",
        "amenities": "Палатки, Спальные мешки, Костровая зона, Гид, Баня, Питание",
        "image": "images/acc-5.svg",
        "gallery": "images/acc-5.svg\nimages/gallery-2.svg",
        "capacity": 4,
    },
    {
        "name": "База отдыха «Алдан»",
        "description": (
            "Уютная база на берегу таёжной реки в Алданском районе. Домики с печным "
            "отоплением, баня по-чёрному и отличная рыбалка. Здесь можно отключиться от "
            "города и провести время на природе всей семьёй."
        ),
        "location": "Алданский район, Алдан",
        "price": 4500,
        "type": "База отдыха",
        "amenities": "Мангал, Баня, Кухня, Парковка, Рыбалка, Детская площадка",
        "image": "images/acc-6.svg",
        "gallery": "images/acc-6.svg\nimages/gallery-1.svg",
        "capacity": 5,
    },
    {
        "name": "Глэмпинг «Тимптон»",
        "description": (
            "Комфортные A-frame домики на берегу Тимптона среди скалистых сопок. "
            "Утром — кофе с видом на реку, днём — сплав или пеший маршрут, вечером — баня "
            "и звёзды. Трансфер из Нерюнгри включён в проживание."
        ),
        "location": "Нерюнгринский район, река Тимптон",
        "price": 7300,
        "type": "Глэмпинг",
        "amenities": "Панорамные окна, Кухня, Баня, Трансфер, Wi-Fi, Экскурсии",
        "image": "images/acc-7.svg",
        "gallery": "images/acc-7.svg\nimages/gallery-3.svg",
        "capacity": 2,
    },
    {
        "name": "Усадьба «Сайсары»",
        "description": (
            "Гостевая усадьба в центре Якутска, в пяти минутах от озера Сайсары. "
            "Аутентичный деревянный дом с современным ремонтом, домашней кухней и тёплым "
            "приёмом. Отличный старт для путешествия по республике."
        ),
        "location": "Якутск, озеро Сайсары",
        "price": 3900,
        "type": "Усадьба",
        "amenities": "Завтрак, Wi-Fi, Парковка, Мангал, Кухня, Детская кроватка",
        "image": "images/acc-8.svg",
        "gallery": "images/acc-8.svg\nimages/gallery-2.svg",
        "capacity": 4,
    },
]


def seed_database():
    """Идемпотентно заполняет базу демонстрационными данными."""
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if admin is None:
        admin = User(
            name="Администратор",
            email=ADMIN_EMAIL,
            phone="+7 914 000-00-01",
            role="admin",
        )
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)

    client = User.query.filter_by(email=CLIENT_EMAIL).first()
    if client is None:
        client = User(
            name="Анна Петрова",
            email=CLIENT_EMAIL,
            phone="+7 914 123-45-67",
            role="client",
        )
        client.set_password(CLIENT_PASSWORD)
        db.session.add(client)

    second_client = User.query.filter_by(email="ivan@example.com").first()
    if second_client is None:
        second_client = User(
            name="Иван Николаев",
            email="ivan@example.com",
            phone="+7 914 765-43-21",
            role="client",
        )
        second_client.set_password(CLIENT_PASSWORD)
        db.session.add(second_client)

    db.session.flush()

    if Accommodation.query.count() == 0:
        for item in ACCOMMODATIONS:
            db.session.add(Accommodation(**item))
        db.session.flush()

    if Booking.query.count() == 0:
        accommodations = Accommodation.query.order_by(Accommodation.id).all()
        today = date.today()
        now = datetime.utcnow()
        bookings = [
            Booking(
                user_id=client.id,
                accommodation_id=accommodations[0].id,
                check_in=today + timedelta(days=7),
                check_out=today + timedelta(days=10),
                status="pending",
                created_at=now - timedelta(days=1),
            ),
            Booking(
                user_id=client.id,
                accommodation_id=accommodations[1].id,
                check_in=today + timedelta(days=14),
                check_out=today + timedelta(days=18),
                status="confirmed",
                created_at=now - timedelta(days=4),
            ),
            Booking(
                user_id=client.id,
                accommodation_id=accommodations[1].id,
                check_in=today - timedelta(days=60),
                check_out=today - timedelta(days=57),
                status="completed",
                created_at=now - timedelta(days=75),
            ),
            Booking(
                user_id=client.id,
                accommodation_id=accommodations[3].id,
                check_in=today + timedelta(days=30),
                check_out=today + timedelta(days=33),
                status="cancelled",
                created_at=now - timedelta(days=8),
            ),
            Booking(
                user_id=second_client.id,
                accommodation_id=accommodations[4].id,
                check_in=today - timedelta(days=30),
                check_out=today - timedelta(days=27),
                status="completed",
                created_at=now - timedelta(days=45),
            ),
        ]
        db.session.add_all(bookings)

    db.session.commit()

    print("Демо-данные готовы.")
    print(f"Администратор: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"Клиент:        {CLIENT_EMAIL} / {CLIENT_PASSWORD}")
    print(f"Объектов размещения: {Accommodation.query.count()}")
    print(f"Бронирований: {Booking.query.count()}")
