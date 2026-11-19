document.addEventListener("DOMContentLoaded", () => {
    initDatePairs();
    initBookingForm();
    initConfirmations();
    initImagePreview();
    initFlashDismiss();
});

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function addDays(value, days) {
    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) {
        return "";
    }
    date.setDate(date.getDate() + days);
    return formatDate(date);
}

function nightsBetween(start, end) {
    if (!start || !end) {
        return 0;
    }
    const startDate = new Date(`${start}T00:00:00`);
    const endDate = new Date(`${end}T00:00:00`);
    const diff = Math.round((endDate - startDate) / 86400000);
    return diff > 0 ? diff : 0;
}

function bindDatePair(checkIn, checkOut) {
    if (!checkIn || !checkOut) {
        return;
    }

    const syncMinimum = () => {
        if (!checkIn.value) {
            checkOut.removeAttribute("min");
            return;
        }
        const nextDay = addDays(checkIn.value, 1);
        checkOut.min = nextDay;
        if (checkOut.value && checkOut.value <= checkIn.value) {
            checkOut.value = nextDay;
        }
    };

    checkIn.addEventListener("change", syncMinimum);
    syncMinimum();
}

function initDatePairs() {
    const pairs = [
        [document.querySelector("#heroCheckIn"), document.querySelector("#heroCheckOut")],
        [document.querySelector("#catalogCheckIn"), document.querySelector("#catalogCheckOut")],
    ];
    pairs.forEach(([checkIn, checkOut]) => bindDatePair(checkIn, checkOut));
}

function nightsWord(number) {
    const lastTwo = number % 100;
    if (lastTwo >= 11 && lastTwo <= 14) {
        return "ночей";
    }
    const last = number % 10;
    if (last === 1) {
        return "ночь";
    }
    if (last >= 2 && last <= 4) {
        return "ночи";
    }
    return "ночей";
}

function initBookingForm() {
    const form = document.querySelector("[data-booking-form]");
    if (!form) {
        return;
    }

    const checkIn = form.querySelector('input[name="check_in"]');
    const checkOut = form.querySelector('input[name="check_out"]');
    const totalBox = form.querySelector("#bookingTotal");
    const totalLabel = form.querySelector("#bookingTotalLabel");
    const totalValue = form.querySelector("#bookingTotalValue");
    const price = Number.parseFloat(form.dataset.price || "0");

    if (!checkIn || !checkOut) {
        return;
    }

    bindDatePair(checkIn, checkOut);

    const updateTotal = () => {
        const nights = nightsBetween(checkIn.value, checkOut.value);
        if (!totalBox || !totalLabel || !totalValue) {
            return;
        }
        if (nights > 0 && price > 0) {
            totalBox.classList.remove("d-none");
            totalLabel.textContent = `Итого за ${nights} ${nightsWord(nights)}`;
            totalValue.textContent = `${new Intl.NumberFormat("ru-RU").format(nights * price)} ₽`;
        } else {
            totalBox.classList.add("d-none");
        }
    };

    checkIn.addEventListener("change", updateTotal);
    checkOut.addEventListener("change", updateTotal);
    updateTotal();
}

function initConfirmations() {
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirm || "Вы уверены?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
}

function initImagePreview() {
    document.querySelectorAll("[data-image-input]").forEach((input) => {
        input.addEventListener("change", () => {
            const file = input.files && input.files[0];
            const previewSelector = input.dataset.preview;
            const preview = previewSelector ? document.querySelector(previewSelector) : null;
            if (file && preview) {
                preview.src = URL.createObjectURL(file);
            }
        });
    });
}

function initFlashDismiss() {
    if (typeof bootstrap === "undefined") {
        return;
    }
    document.querySelectorAll(".flash-container .alert").forEach((alert) => {
        window.setTimeout(() => {
            const instance = bootstrap.Alert.getOrCreateInstance(alert);
            instance.close();
        }, 8000);
    });
}
