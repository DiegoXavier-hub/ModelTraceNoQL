from __future__ import annotations

import re


MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
SPECIAL_CHARACTER_PATTERN = re.compile(r"[^A-Za-z0-9]")
COMMON_WEAK_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "senha",
    "senha123",
    "admin",
    "admin123",
    "qwerty",
    "qwerty123",
    "secret",
    "secret123",
    "modeltrace",
}


def password_strength_errors(
    password: str,
    *,
    email: str | None = None,
    name: str | None = None,
    organization_name: str | None = None,
) -> list[str]:
    errors: list[str] = []
    normalized = password.lower()

    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"use at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"use at most {MAX_PASSWORD_LENGTH} characters")
    if not any(character.islower() for character in password):
        errors.append("include a lowercase letter")
    if not any(character.isupper() for character in password):
        errors.append("include an uppercase letter")
    if not any(character.isdigit() for character in password):
        errors.append("include a number")
    if not SPECIAL_CHARACTER_PATTERN.search(password):
        errors.append("include a special character")
    if normalized in COMMON_WEAK_PASSWORDS:
        errors.append("avoid common passwords")
    if len(set(normalized)) <= 3:
        errors.append("avoid repeated characters")

    profile_terms = _profile_terms(email=email, name=name, organization_name=organization_name)
    if any(term and len(term) >= 4 and term in normalized for term in profile_terms):
        errors.append("avoid using name, email or organization terms")

    return errors


def _profile_terms(*, email: str | None, name: str | None, organization_name: str | None) -> set[str]:
    terms: set[str] = set()
    if email:
        local_part = email.split("@", 1)[0]
        terms.update(_split_terms(local_part))
    if name:
        terms.update(_split_terms(name))
    if organization_name:
        terms.update(_split_terms(organization_name))
    return {term.lower() for term in terms if term}


def _split_terms(value: str) -> set[str]:
    return {term for term in re.split(r"[^A-Za-z0-9]+", value.lower()) if term}
