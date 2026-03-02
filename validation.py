"""
payment_validation.py

Skeleton file for input validation exercise.
You must implement each validation function according to the
specification provided in the docstrings.

All validation functions must return:

    (clean_value, error_message)

Where:
    clean_value: normalized/validated value (or empty string if invalid)
    error_message: empty string if valid, otherwise error description
"""

import re
import unicodedata
from datetime import datetime
from typing import Tuple, Dict


# =============================
# Regular Patterns
# =============================


CARD_DIGITS_RE = re.compile(r"^\d+$")     # digits only
CVV_RE = re.compile(r"^\d{3,4}$")             # 3 or 4 digits
EXP_RE = re.compile(r"^(0[1-9]|1[0-2])\/\d{2}$")             # MM/YY format
EMAIL_BASIC_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")     # basic email structure
NAME_ALLOWED_RE = re.compile(r"^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s'\-]+$")    # allowed name characters with accents


# =============================
# Utility Functions
# =============================

def normalize_basic(value: str) -> str:

    """
    Normalize input using NFKC and strip whitespace.
    """

    return unicodedata.normalize("NFKC", (value or "")).strip()


def luhn_is_valid(number: str) -> bool:
    """
    ****BONUS IMPLEMENTATION****

    Validate credit card number using Luhn algorithm.

    Input:
        number (str) -> digits only

    Returns:
        True if valid according to Luhn algorithm
        False otherwise
    """
    if not number.isdigit():
        return False
    
    total = 0
    reverse = number[::-1]
    for i, digito in enumerate(reverse):
        n = int(digito)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

    pass


# =============================
# Field Validations
# =============================

def validate_card_number(card_number: str) -> Tuple[str, str]:
    """
    Validate credit card number.

    Requirements:
    - Normalize input
    - Remove spaces and hyphens before validation
    - Must contain digits only
    - Length between 13 and 19 digits
    - BONUS: Must pass Luhn algorithm

    Input:
        card_number (str)

    Returns:
        (card, error_message)

    Notes:
        - If invalid → return ("", "Error message")
        - If valid → return (all credit card digits, "")
    """
    str_normalized = normalize_basic(card_number)
    str_spaces_removed = str_normalized.replace(" ", "").replace("-", "")

    if not CARD_DIGITS_RE.match(str_spaces_removed):
        return "", "The card number must contain digits only"
    if not (13 <= len(str_spaces_removed) <= 19):
        return "", "The card number must be between 13 and 19 digits long   "
        
    # Optional Luhn check
    if not luhn_is_valid(str_spaces_removed):
        return "", "The card number is not valid according to the Luhn algorithm"

    # TODO: Implement validation
    return str_spaces_removed, ""


def validate_exp_date(exp_date: str) -> Tuple[str, str]:

    # Format MM/YY


    """
    Validate expiration date.

    Requirements:
    - Format must be MM/YY
    - Month must be between 01 and 12
    - Must not be expired compared to current UTC date
    - Optional: limit to reasonable future (e.g., +15 years)

    Input:
        exp_date (str)

    Returns:
        (normalized_exp_date, error_message)
    """
    if not exp_date:
        return "", "Expiration date is required"
    
    exp_date = exp_date.strip()
    """
    CVV_RE = re.compile(r"^\d{3,4}$")             # 3 or 4 digits
    """
    #Fomat check
    if not EXP_RE.match(exp_date):
        return "", "Expiration date must be in MM/YY format"
    
    #month betwen 01 and 12
    month, year = exp_date.split("/")
    if not (1 <= int(month) <= 12):
        return "", "Expiration month must be between 01 and 12"
    
    #Must not be expired compared to current UTC date
    current_year = datetime.utcnow().year % 100  # Get last two digits of current year
    current_month = datetime.utcnow().month
    if int(year) < current_year or (int(year) == current_year and int(month) < current_month):
        return "", "Card is expired"
    
    normalized_exp_date = f"{month}/{year}"
    
    return normalized_exp_date, ""


def validate_cvv(cvv: str) -> Tuple[str, str]:
    """
    Validate CVV.

    Requirements:
    - Must contain only digits
    - Must be exactly 3 or 4 digits

    Input:
        cvv (str)

    Returns:
        ("", error_message)
        (always return empty clean value for security reasons)
    """

    if not cvv:
        return "", "CVV is required"
    #Must contain only digits
    if not cvv.isdigit():
        return "", "CVV must contain digits only"
    #Must be exactly 3 or 4 digits
    if not CVV_RE.match(cvv):
        return "", "CVV must be 3 or 4 digits"
    
    #Should NOT return the CVV value for storage


    return "", ""


def validate_billing_email(billing_email: str) -> Tuple[str, str]:
    """
    Validate billing email.

    Requirements:
    - Normalize (strip + lowercase)
    - Max length 254
    - Must match basic email pattern

    Input:
        billing_email (str)

    Returns:
        (normalized_email, error_message)
    """

    normalized_email = normalize_basic(billing_email).lower()
    if len(normalized_email) > 254:
        return "", "Email must be at most 254 characters long"
    if not EMAIL_BASIC_RE.match(normalized_email):
        return "", "Email format is invalid"

    # TODO: Implement validation
    return normalized_email, ""


def validate_name_on_card(name_on_card: str) -> Tuple[str, str]:
    """
    Validate name on card.

    Requirements:
    - 
    - Collapse multiple spaces
    - Length between 2 and 60 characters
    - Only letters (including accents), spaces, apostrophes, hyphens

    Input:
        name_on_card (str)

    Returns:
        (normalized_name, error_message)
    """
    # Normalize input
    normalized_name = normalize_basic(name_on_card)
    # Collapse multiple spaces
    normalized_name = re.sub(r"\s+", " ", normalized_name)
    # Length check
    if not (2 <= len(normalized_name) <= 60):
        return "", "Name on card must be between 2 and 60 characters long"
    # Character check
    if not NAME_ALLOWED_RE.match(normalized_name):
        return "", "Name on card contains invalid characters"

    return normalized_name, ""


# =============================
# Orchestrator Function
# =============================

def validate_payment_form(
    card_number: str,
    exp_date: str,
    cvv: str,
    name_on_card: str,
    billing_email: str
) -> Tuple[Dict, Dict]:
    """
    Orchestrates all field validations.

    Returns:
        clean (dict)  -> sanitized values safe for storage/use
        errors (dict) -> field_name -> error_message
    """

    clean = {}
    errors = {}

    card, err = validate_card_number(card_number)
    if err:
        errors["card_number"] = err
    clean["card"] = card

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