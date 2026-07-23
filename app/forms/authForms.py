from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


def _strip(value):
    return value.strip() if value else value


def _strip_lower(value):
    return value.strip().lower() if value else value


class RegisterForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=120)],
        filters=[_strip],
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=30),
            Regexp(
                r"^[A-Za-z0-9_]+$",
                message="Use only letters, numbers, and underscores.",
            ),
        ],
        filters=[_strip_lower],
    )
    email = StringField(
        "Email address",
        validators=[
            DataRequired(),
            Length(max=254),
            Regexp(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                message="Enter a valid email address.",
            ),
        ],
        filters=[_strip_lower],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128, message="Use between 8 and 128 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField(
        "Email address",
        validators=[DataRequired(), Length(max=254)],
        filters=[_strip_lower],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(max=128)],
    )
    remember = BooleanField("Keep me signed in")
    submit = SubmitField("Log in")
