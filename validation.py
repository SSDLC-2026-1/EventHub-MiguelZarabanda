import re
import unicodedata
from datetime import datetime
from typing import Dict, Tuple

CARD_DIGITS_RE = re.compile(r"^\d+$")
CVV_RE = re.compile(r"^\d{3,4}$")
EXP_RE = re.compile(r"^(0[1-9]|1[0-2])\/(\d{2})$")
EMAIL_BASIC_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NAME_ALLOWED_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$")


def normalize_basic(s: str) -> str:
    return unicodedata.normalize("NFKC", (s or "")).strip()


def luhn_is_valid(number: str) -> bool:
    total = 0
    for i, ch in enumerate(number[::-1]):
        d = ord(ch) - ord("0")
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def validate_card_number(card_number: str) -> Tuple[str, str]:
    raw = normalize_basic(card_number)
    digits = re.sub(r"[\s-]+", "", raw)
    if not digits:
        return "", "Card number is required."
    if not CARD_DIGITS_RE.fullmatch(digits):
        return "", "Card number must contain digits only."
    if not (13 <= len(digits) <= 19):
        return "", "Card number must be 13 to 19 digits."
    if not luhn_is_valid(digits):
        return "", "Card number is invalid."
    return digits[-4:], ""


def validate_exp_date(exp_date: str) -> Tuple[str, str]:
    exp = normalize_basic(exp_date)
    if not exp:
        return "", "Expiration date is required."
    m = EXP_RE.fullmatch(exp)
    if not m:
        return "", "Use format MM/YY (e.g., 09/28)."
    mm = int(m.group(1))
    yy = int(m.group(2))
    year = 2000 + yy
    now = datetime.utcnow()
    if (year, mm) < (now.year, now.month):
        return "", "Card is expired."
    if (year, mm) > (now.year + 15, now.month):
        return "", "Expiration date is not valid."
    return exp, ""


def validate_cvv(cvv: str) -> Tuple[str, str]:
    v = normalize_basic(cvv)
    if not v:
        return "", "CVV is required."
    if not CVV_RE.fullmatch(v):
        return "", "CVV must be 3 or 4 digits."
    return "", ""


def validate_billing_email(billing_email: str) -> Tuple[str, str]:
    email = normalize_basic(billing_email).lower()
    if not email:
        return "", "Billing email is required."
    if len(email) > 254:
        return "", "Billing email is too long."
    if not EMAIL_BASIC_RE.fullmatch(email):
        return "", "Enter a valid email (e.g., name@example.com)."
    return email, ""


def validate_name_on_card(name_on_card: str) -> Tuple[str, str]:
    name = normalize_basic(name_on_card)
    name = re.sub(r"\s{2,}", " ", name)
    if not name:
        return "", "Name on card is required."
    if not (2 <= len(name) <= 60):
        return "", "Name must be 2 to 60 characters."
    if not NAME_ALLOWED_RE.fullmatch(name):
        return "", "Name can only include letters, spaces, apostrophes, and hyphens."
    return name, ""


def validate_payment_form(card_number: str, exp_date: str, cvv: str, name_on_card: str, billing_email: str) -> Tuple[Dict, Dict]:
    clean = {}
    errors = {}

    last4, err = validate_card_number(card_number)
    if err:
        errors["card_number"] = err
    clean["card_last4"] = last4

    exp_clean, err = validate_exp_date(exp_date)
    if err:
        errors["exp_date"] = err
    clean["exp_date"] = exp_clean

    _, err = validate_cvv(cvv)
    if err:
        errors["cvv"] = err

    name_clean, err = validate_name_on_card(name_on_card)
    if err:
        errors["name_on_card"] = err
    clean["name_on_card"] = name_clean

    email_clean, err = validate_billing_email(billing_email)
    if err:
        errors["billing_email"] = err
    clean["billing_email"] = email_clean

    return clean, errors
