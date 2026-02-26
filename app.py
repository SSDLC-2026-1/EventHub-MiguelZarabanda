from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import re
from typing import List, Optional, Dict

from flask import Flask, render_template, request, abort, url_for, redirect, session
from functools import wraps
from pathlib import Path
import time 
import json

from validation import validate_payment_form
from encryption import verify_password
from encryption import hash_password

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "dev-secret-change-me"


BASE_DIR = Path(__file__).resolve().parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"
USERS_PATH = BASE_DIR / "data" / "users.json"
ORDERS_PATH = BASE_DIR / "data" / "orders.json"
CATEGORIES = ["All", "Music", "Tech", "Sports", "Business"]
CITIES = ["Any", "New York", "San Francisco", "Berlin", "London", "Oakland", "San Jose"]

Max_attempts = 3
Lock_time = 300
user_attempts = {}

@dataclass(frozen=True)
class Event:
    id: int
    title: str
    category: str  
    city: str
    venue: str
    start: datetime
    end: datetime
    price_usd: float
    available_tickets: int
    banner_url: str
    description: str

def _user_with_defaults(u: dict) -> dict:
    u = dict(u)
    u.setdefault("role", "user")      
    u.setdefault("status", "active")  
    u.setdefault("locked_until", "") 
    return u

def get_current_user() -> Optional[dict]:
    email = session.get("user_email")
    if not email:
        return None
    return find_user_by_email(email)


def require_login(roles: Optional[List[str]] = None):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                session.clear()
                return redirect(url_for("login"))

            if roles:
                user_role = (user.get("role") or "user").strip().lower()
                allowed = [r.strip().lower() for r in roles]
                if user_role not in allowed:
                    abort(403)

            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.context_processor
def inject_user():
    """Hacer el  `current_user` y `is_admin` disponible en todas las plantillas."""
    user = get_current_user()
    is_admin = False
    if user:
        is_admin = (user.get("role") or "user").strip().lower() == "admin"
    return {"current_user": user, "is_admin": is_admin}



def load_events() -> List[Event]:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    return [
        Event(
            id=int(e["id"]),
            title=e["title"],
            category=e["category"],
            city=e["city"],
            venue=e["venue"],
            start=datetime.fromisoformat(e["start"]),
            end=datetime.fromisoformat(e["end"]),
            price_usd=float(e["price_usd"]),
            available_tickets=int(e["available_tickets"]),
            banner_url=e.get("banner_url", ""),
            description=e.get("description", ""),
        )
        for e in data
    ]


EVENTS: List[Event] = load_events()


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parsea fecha estilo YYYY-MM-DD. Devuelve None si inválida."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def _safe_int(value: str, default: int = 1, min_v: int = 1, max_v: int = 10) -> int:
    """Validación simple de enteros para inputs (cantidad, etc.)."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, n))


def filter_events(
    q: str = "",
    city: str = "Any",
    date: Optional[datetime] = None,
    category: str = "All",
    ) -> List[Event]:
    q_norm = (q or "").strip().lower()
    city_norm = (city or "Any").strip()
    category_norm = (category or "All").strip()

    results = load_events()

    if category_norm != "All":
        results = [e for e in results if e.category == category_norm]

    if city_norm != "Any":
        results = [e for e in results if e.city == city_norm]

    if date:
        results = [
            e for e in results
            if e.start.date() == date.date()
        ]

    if q_norm:
        results = [
            e for e in results
            if q_norm in e.title.lower() or q_norm in e.venue.lower()
        ]

    results.sort(key=lambda e: e.start)
    return results


def get_event_or_404(event_id: int) -> Event:
    for e in EVENTS:
        if e.id == event_id:
            return e
    abort(404)


def load_users() -> list[dict]:
    if not USERS_PATH.exists():
        USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        USERS_PATH.write_text("[]", encoding="utf-8")
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def save_users(users: list[dict]) -> None:
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def find_user_by_email(email: str) -> Optional[dict]:
    users = load_users()
    email_norm = (email or "").strip().lower()
    for u in users:
        if (u.get("email", "") or "").strip().lower() == email_norm:
            return u
    return None


def user_exists(email: str) -> bool:
    return find_user_by_email(email) is not None

def load_orders() -> list[dict]:
    if not ORDERS_PATH.exists():
        ORDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ORDERS_PATH.write_text("[]", encoding="utf-8")
    return json.loads(ORDERS_PATH.read_text(encoding="utf-8"))


def save_orders(orders: list[dict]) -> None:
    ORDERS_PATH.write_text(json.dumps(orders, indent=2), encoding="utf-8")


def next_order_id(orders: list[dict]) -> int:
    return max([o.get("id", 0) for o in orders], default=0) + 1


# -----------------------------
# Rutas
# -----------------------------
@app.get("/")
def index():
    q = request.args.get("q", "")
    city = request.args.get("city", "Any")
    date_str = request.args.get("date", "")
    category = request.args.get("category", "All")

    date = _parse_date(date_str)
    events = filter_events(q=q, city=city, date=date, category=category)

    featured = events[:3] 
    upcoming = events[:6]

    return render_template(
        "index.html",
        q=q,
        city=city,
        date_str=date_str,
        category=category,
        categories=CATEGORIES,
        cities=CITIES,
        featured=featured,
        upcoming=upcoming,
    )


@app.get("/event/<int:event_id>")
def event_detail(event_id: int):
    event = next((e for e in load_events() if e.id == event_id), None)
    if not event:
        abort(404)

    similar = [e for e in EVENTS if e.category == event.category and e.id != event.id][:5]

    return render_template(
        "event_detail.html",
        event=event,
        similar=similar,
    )


@app.post("/event/<int:event_id>/buy")
def buy_ticket(event_id: int):
    event = get_event_or_404(event_id) 
    qty = _safe_int(request.form.get("qty", "1"), default=1, min_v=1, max_v=8)

    if qty > event.available_tickets:
        similar = [e for e in load_events() if e.category == event.category and e.id != event.id][:5]
        return render_template(
            "event_detail.html",
            event=event,
            similar=similar,
            buy_error="Not enough tickets available for that quantity."
        ), 400

    return redirect(url_for("checkout", event_id=event.id, qty=qty))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        registered = request.args.get("registered")
        msg = "Account created successfully. Please sign in." if registered == "1" else None
        return render_template("login.html", info_message=msg)

    email = request.form.get("email", "")
    password = request.form.get("password", "")

    from validation import validate_billing_email
    field_errors = {}
    email_clean, email_err = validate_billing_email(email)
    if email_err:
        field_errors["email"] = email_err
    if not password.strip():
        field_errors["password"] = "Password is required."

    now = time.time()
    if email in user_attempts and user_attempts[email].get("locked_until", 0) > now:
        remaining = int(user_attempts[email].get('locked_until', 0) - now)
        field_errors["email"] = f"Account is temporarily locked due to multiple failed login attempts. Please try again later. Remaining time: {remaining} seconds."

    if field_errors:
        return render_template(
            "login.html",
            error="Please fix the highlighted fields.",
            field_errors=field_errors,
            form={"email": email},
        ), 400

    user = find_user_by_email(email_clean)
    if not user or user.get("password") != password:
        if user:
            if email not in user_attempts:
                user_attempts[email] = {"attempts": 0, "locked_until": 0}
            user_attempts[email]["attempts"] += 1
            if user_attempts[email]["attempts"] >= Max_attempts:
                user_attempts[email]["locked_until"] = now + Lock_time
        return render_template(
            "login.html",
            error="Invalid credentials.",
            field_errors={"email": " ", "password": " "},
            form={"email": email},
        ), 401

    user_attempts[email] = {"attempts": 0, "locked_until": 0}
    session["user_email"] = email_clean
    return redirect(url_for("dashboard"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", form={})

    full_name = request.form.get("full_name", "")
    email = request.form.get("email", "")
    phone = request.form.get("phone", "")
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    field_errors = {}

    if not full_name.strip():
        field_errors["full_name"] = "Full name is required."
    elif len(full_name) < 2 or len(full_name) > 60:
        field_errors["full_name"] = "Full name must be between 2 and 60 characters."
    else: 
        normalized_name = re.sub(r'\s+', ' ', full_name)  # Collapse multiple spaces
        if not re.match(r"^[a-zA-ZÀ-ÿ\s'-]+$", normalized_name):
            field_errors["full_name"] = "Full name can only contain letters, spaces, apostrophes, and hyphens."
        else:
            full_name = normalized_name
            
    if not email:
        field_errors["email"] = "Email is required."
    elif len(email) > 254:
        field_errors["email"] = "Email must be 254 characters or less."
    elif not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):  # Basic format: one @, domain with .
        field_errors["email"] = "Email must be in a valid format (e.g., user@example.com)."
    elif user_exists(email):
        field_errors["email"] = "An account with this email already exists."

    if not phone:
        field_errors["phone"] = "Phone number is required."
    elif not re.match(r"^\d{7,15}$", phone):  # Only digits, 7-15 length
        field_errors["phone"] = "Phone number must contain only digits and be 7-15 characters long."

    if not password:
        field_errors["password"] = "Password is required."
    elif len(password) < 8 or len(password) > 64:
        field_errors["password"] = "Password must be between 8 and 64 characters."
    elif " " in password:
        field_errors["password"] = "Password cannot contain spaces."
    elif password == email:
        field_errors["password"] = "Password cannot be the same as your email."
    elif not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-=\+\[\]{}<>?]).+$", password):
        field_errors["password"] = "Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character (!@#$%^&*()_-+=[]{}<>?)."
    elif password != confirm_password:
        field_errors["confirm_password"] = "Passwords do not match."

    if field_errors:
        return render_template(
            "register.html",
            error="Please fix the highlighted fields.",
            field_errors=field_errors,
            form={"full_name": full_name, "email": email, "phone": phone},
        ), 400


    users = load_users()
    hashed_pwd = hash_password(password)
    new_user = {
        "id": len(users) + 1,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "password": hashed_pwd,  # Guardar el dict generado
        "role": "user",
        "status": "active",
    }
    users.append(new_user)
    save_users(users)

    return redirect(url_for("login", registered="1"))

@app.get("/dashboard")
@require_login()
def dashboard():
    paid = request.args.get("paid") == "1"
    user = get_current_user()
    return render_template("dashboard.html", user_name=(user.get("full_name") if user else "User"), paid=paid)

@app.route("/checkout/<int:event_id>", methods=["GET", "POST"])
@require_login()
def checkout(event_id: int):


    events = load_events()
    event = next((e for e in events if e.id == event_id), None)
    if not event:
        abort(404)

    qty = _safe_int(request.args.get("qty", "1"), default=1, min_v=1, max_v=8)

    service_fee = 5.00
    subtotal = event.price_usd * qty
    total = subtotal + service_fee

    if request.method == "GET":
        return render_template(
            "checkout.html",
            event=event,
            qty=qty,
            subtotal=subtotal,
            service_fee=service_fee,
            total=total,
            errors={},
            form_data={}
        )

    card_number = request.form.get("card_number", "")
    exp_date = request.form.get("exp_date", "")
    cvv = request.form.get("cvv", "")
    name_on_card = request.form.get("name_on_card", "")
    billing_email = request.form.get("billing_email", "")

    clean, errors = validate_payment_form(
        card_number=card_number,
        exp_date=exp_date,
        cvv=cvv,
        name_on_card=name_on_card,
        billing_email=billing_email
    )

    form_data = {
        "exp_date": clean.get("exp_date", ""),
        "name_on_card": clean.get("name_on_card", ""),
        "billing_email": clean.get("billing_email", ""),
        "card": clean.get("card", "")
    }

    if errors:
        return render_template(
            "checkout.html",
            event=event, qty=qty, subtotal=subtotal,
            service_fee=service_fee, total=total,
            errors=errors, form_data=form_data
        ), 400

    orders = load_orders()
    order_id = next_order_id(orders)

    orders.append({
        "id": order_id,
        "user_email": "PLACEHOLDER@EMAIL.COM",
        "event_id": event.id,
        "event_title": event.title,
        "qty": qty,
        "unit_price": event.price_usd,
        "service_fee": service_fee,
        "total": total,
        "status": "PAID",
        "created_at": datetime.utcnow().isoformat(),
        "payment": form_data
    })

    save_orders(orders)

    return redirect(url_for("dashboard", paid="1"))



@app.route("/profile", methods=["GET", "POST"])
@require_login()
def profile():

    user = get_current_user()

    form = {
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
    }

    field_errors = {}  
    success_msg = None

    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        phone = request.form.get("phone", "")

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_new_password = request.form.get("confirm_new_password", "")

        field_errors = {}

        if not full_name.strip():
            field_errors["full_name"] = "Full name is required."
        elif len(full_name) < 2 or len(full_name) > 60:
            field_errors["full_name"] = "Full name must be between 2 and 60 characters."
        else:
            normalized_name = re.sub(r'\s+', ' ', full_name).strip()
            if not re.match(r"^[a-zA-ZÀ-ÿ\s'-]+$", normalized_name):
                field_errors["full_name"] = "Full name can only contain letters, spaces, apostrophes, and hyphens."
            else:
                full_name = normalized_name

        if not phone.strip().lower():
            field_errors["phone"] = "Phone number is required."
        elif not re.match(r"^\d{7,15}$", phone):
            field_errors["phone"] = "Phone number must contain only digits and be 7-15 characters long."

        if new_password:
            if not current_password:
                field_errors["current_password"] = "Current password is required to change your password."
            elif current_password == new_password:
                field_errors["new_password"] = "The new password must be different from the current password."
            else:
                stored_pw = user.get("password", "")
                if current_password != stored_pw:
                    field_errors["current_password"] = "Current password is incorrect."

            if "new_password" not in field_errors:
                if len(new_password) < 8 or len(new_password) > 64:
                    field_errors["new_password"] = "Password must be between 8 and 64 characters."
                elif " " in new_password:
                    field_errors["new_password"] = "Password cannot contain spaces."
                elif new_password == (user.get("email") or ""):
                    field_errors["new_password"] = "Password cannot be the same as your email."
                elif not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-\=\+\[\]{}<>?]).+$", new_password):
                    field_errors["new_password"] = "Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character (!@#$%^&*()_-+=[]{}<>?)."
                elif new_password != confirm_new_password:
                    field_errors["confirm_new_password"] = "Passwords do not match."

        if field_errors:
            form["full_name"] = full_name
            form["phone"] = phone
            field_errors_local = field_errors
            return render_template(
                "profile.html",
                form=form,
                field_errors=field_errors_local,
                success_message=None,
            ), 400

        # Persistir cambios solo si todo es válido
        users = load_users()
        email_norm = (user.get("email") or "").strip().lower()

        for u in users:
            if (u.get("email") or "").strip().lower() == email_norm:
                u["full_name"] = full_name
                u["phone"] = phone
                if new_password:
                    u["password"] = new_password
                break

        save_users(users)

        form["full_name"] = full_name
        form["phone"] = phone
        success_msg = "Profile updated successfully."

    return render_template(
        "profile.html",
        form=form,
        field_errors=field_errors,
        success_message=success_msg,
    )
@app.get("/admin/users")
@require_login(roles=["admin"])
def admin_users():

    q = (request.args.get("q") or "").strip().lower()
    role = (request.args.get("role") or "all").strip().lower()
    status = (request.args.get("status") or "all").strip().lower()
    lockout = (request.args.get("lockout") or "all").strip().lower()

    users = [_user_with_defaults(u) for u in load_users()]

    # filtros
    if q:
        users = [
            u for u in users
            if q in (u.get("full_name","").lower()) or q in (u.get("email","").lower())
        ]

    if role != "all":
        users = [u for u in users if (u.get("role","user").lower() == role)]

    if status != "all":
        users = [u for u in users if (u.get("status","active").lower() == status)]

    if lockout != "all":
        if lockout == "locked":
            users = [u for u in users if (u.get("locked_until") or "").strip()]
        elif lockout == "not_locked":
            users = [u for u in users if not (u.get("locked_until") or "").strip()]

    users.sort(key=lambda u: (u.get("full_name","").lower(), u.get("id", 0)))

    return render_template(
        "admin_users.html",
        users=users,
        filters={"q": q, "role": role, "status": status, "lockout": lockout},
        total=len(users),
    )

@app.post("/admin/users/<int:user_id>/toggle")
def admin_toggle_user(user_id: int):
    users = load_users()
    for u in users:
        if int(u.get("id", 0)) == user_id:
            u.setdefault("status", "active")
            u["status"] = "disabled" if u["status"] == "active" else "active"
            break
    save_users(users)
    return redirect(url_for("admin_users"))

@app.post("/admin/users/<int:user_id>/role")
def admin_change_role(user_id: int):
    new_role = request.form.get("role", "user")

    users = load_users()
    for u in users:
        if int(u.get("id", 0)) == user_id:
            u["role"] = new_role
            break
    save_users(users)
    return redirect(url_for("admin_users"))

@app.route("/logout")
def logout():
    session.clear()  # Limpia toda la sesión
    return redirect(url_for("index"))

def password_encryption(password: str) -> dict:
    
    password_byters = password.encode()
    cipher = AES.new(get_random_bytes(16), AES.MODE_GCM)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(password_byters)

    return {
        "ciphertext": ciphertext.hex(),
        "nonce": nonce.hex(),
        "tag": tag.hex()
    }




if __name__ == "__main__":
    app.run(debug=True)





