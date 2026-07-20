import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta

from flask import current_app
from mysql.connector import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.repository import userRepository
from app.services.emailService import EmailDeliveryError, send_verification_code


class RegistrationConflict(Exception):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field
        self.message = message


class VerificationError(ValueError):
    pass


class VerificationExpired(VerificationError):
    pass


class VerificationLocked(VerificationError):
    pass


class ResendTooSoon(VerificationError):
    pass


class GoogleAuthenticationError(ValueError):
    pass


_DUMMY_PASSWORD_HASH = generate_password_hash("madeby-invalid-password")


def _now():
    return datetime.now(UTC).replace(tzinfo=None)


def _new_code():
    return f"{secrets.randbelow(1_000_000):06d}"


def _code_hash(email, code):
    payload = f"{email.lower()}:{code}".encode()
    secret = current_app.config["SECRET_KEY"].encode()
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def start_email_registration(full_name, username, email, password):
    conflicts = userRepository.find_registration_conflicts(username, email)
    if any(row["email"].lower() == email for row in conflicts):
        raise RegistrationConflict(
            "email", "An account with this email already exists."
        )
    if conflicts:
        raise RegistrationConflict("username", "This username is already taken.")

    pending_conflicts = userRepository.find_pending_conflicts(username, email)
    if any(
        row["username"].lower() == username and row["email"].lower() != email
        for row in pending_conflicts
    ):
        raise RegistrationConflict("username", "This username is already taken.")

    code = _new_code()
    now = _now()
    try:
        userRepository.save_pending_registration(
            full_name=full_name,
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            code_hash=_code_hash(email, code),
            expires_at=now + timedelta(minutes=10),
            resend_available_at=now + timedelta(seconds=60),
        )
        send_verification_code(email, code)
    except EmailDeliveryError:
        userRepository.delete_pending_registration(email)
        raise
    except IntegrityError as error:
        raise RegistrationConflict(
            "username", "This username is already taken."
        ) from error
    return email


def verify_email_registration(email, code):
    pending = userRepository.find_pending_by_email(email)
    if not pending:
        raise VerificationExpired("Start registration again.")
    if pending["attempts"] >= 5:
        raise VerificationLocked("Too many incorrect attempts. Request a new code.")
    if pending["expires_at"] < _now():
        raise VerificationExpired("This code has expired. Request a new one.")

    submitted_hash = _code_hash(email, code)
    if not hmac.compare_digest(pending["code_hash"], submitted_hash):
        userRepository.record_verification_attempt(email)
        raise VerificationError("That verification code is incorrect.")

    try:
        user_id = userRepository.complete_pending_registration(
            email, submitted_hash
        )
    except IntegrityError as error:
        raise RegistrationConflict(
            "email", "This account has already been created."
        ) from error
    if not user_id:
        raise VerificationError("The verification code is no longer valid.")
    return user_id


def resend_verification_code(email):
    pending = userRepository.find_pending_by_email(email)
    if not pending:
        raise VerificationExpired("Start registration again.")
    now = _now()
    if pending["resend_available_at"] > now:
        raise ResendTooSoon("Please wait before requesting another code.")

    code = _new_code()
    send_verification_code(email, code)
    userRepository.update_pending_code(
        email,
        _code_hash(email, code),
        now + timedelta(minutes=10),
        now + timedelta(seconds=60),
    )


def login_or_create_google_user(userinfo):
    subject = str(userinfo.get("sub") or "")
    email = str(userinfo.get("email") or "").strip().lower()
    if not subject or not email or not userinfo.get("email_verified"):
        raise GoogleAuthenticationError(
            "Google did not provide a verified email address."
        )

    user = userRepository.find_by_google_subject(subject)
    if user:
        if user["account_status"] != "active":
            raise GoogleAuthenticationError("This MadeBy account is disabled.")
        return user

    existing = userRepository.find_by_email(email)
    if existing:
        if existing["account_status"] != "active":
            raise GoogleAuthenticationError("This MadeBy account is disabled.")
        userRepository.link_google_identity(existing["user_id"], subject)
        return existing

    name = str(userinfo.get("name") or email.split("@", 1)[0]).strip()[:120]
    base = re.sub(r"[^a-z0-9_]", "_", email.split("@", 1)[0].lower()).strip("_")
    base = (base or "maker")[:24]
    if len(base) < 3:
        base = f"{base}_user"
    username = base
    while userRepository.username_exists(username):
        username = f"{base[:23]}_{secrets.randbelow(1_000_000):06d}"

    user_id = userRepository.create_google_user(
        full_name=name,
        username=username,
        email=email,
        password_hash=generate_password_hash(secrets.token_urlsafe(48)),
        subject=subject,
    )
    return {
        "user_id": user_id,
        "full_name": name,
        "role": "user",
        "account_status": "active",
    }


def authenticate_user(email, password):
    user = userRepository.find_by_email(email)
    password_hash = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
    password_matches = check_password_hash(password_hash, password)
    if not user or not password_matches:
        return None
    if user["account_status"] != "active":
        return None
    return user
