import smtplib
from email.message import EmailMessage

from flask import current_app


class EmailDeliveryError(RuntimeError):
    pass


def send_verification_code(recipient, code):
    _send_email(
        recipient,
        f"{code} is your MadeBy verification code",
        "Welcome to MadeBy.\n\n"
        f"Your verification code is: {code}\n\n"
        "This code expires in 10 minutes. If you did not request it, "
        "you can ignore this email.",
    )


def send_password_reset_code(recipient, code):
    _send_email(
        recipient,
        f"{code} is your MadeBy password reset code",
        "A password reset was requested for your MadeBy account.\n\n"
        f"Your password reset code is: {code}\n\n"
        "This single-use code expires in 10 minutes. If you did not request "
        "a password reset, you can ignore this email and keep your current password.",
    )


def _send_email(recipient, subject, body):
    if current_app.config["MAIL_SUPPRESS_SEND"]:
        return

    host = current_app.config["SMTP_HOST"]
    sender = current_app.config["SMTP_FROM_EMAIL"]
    if not host or not sender:
        raise EmailDeliveryError("Email delivery is not configured.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    try:
        if current_app.config["SMTP_USE_SSL"]:
            smtp = smtplib.SMTP_SSL(
                host,
                current_app.config["SMTP_PORT"],
                timeout=15,
            )
        else:
            smtp = smtplib.SMTP(
                host,
                current_app.config["SMTP_PORT"],
                timeout=15,
            )
        with smtp:
            if current_app.config["SMTP_USE_TLS"] and not current_app.config["SMTP_USE_SSL"]:
                smtp.starttls()
            username = current_app.config["SMTP_USERNAME"]
            if username:
                smtp.login(username, current_app.config["SMTP_PASSWORD"])
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        current_app.logger.exception("Could not send a verification email")
        raise EmailDeliveryError("The verification email could not be sent.") from error
