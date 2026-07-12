from mysql.connector import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.repository import userRepository


class RegistrationConflict(Exception):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field
        self.message = message


_DUMMY_PASSWORD_HASH = generate_password_hash("madeby-invalid-password")


def register_user(full_name, username, email, password):
    conflicts = userRepository.find_registration_conflicts(username, email)
    if any(row["email"].lower() == email for row in conflicts):
        raise RegistrationConflict(
            "email", "An account with this email already exists."
        )
    if conflicts:
        raise RegistrationConflict("username", "This username is already taken.")

    try:
        return userRepository.create_user(
            full_name=full_name,
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
    except IntegrityError as error:
        # The database constraint remains the final guard against concurrent signups.
        message = str(error).lower()
        field = "email" if "email" in message else "username"
        friendly = (
            "An account with this email already exists."
            if field == "email"
            else "This username is already taken."
        )
        raise RegistrationConflict(field, friendly) from error


def authenticate_user(email, password):
    user = userRepository.find_by_email(email)
    password_hash = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
    password_matches = check_password_hash(password_hash, password)
    if not user or not password_matches:
        return None
    if user["account_status"] != "active":
        return None
    return user
