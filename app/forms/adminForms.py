from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class SuspendUserForm(FlaskForm):
    duration = IntegerField(
        "Duration",
        validators=[DataRequired(), NumberRange(min=1, max=8760)],
    )
    unit = SelectField(
        "Unit",
        choices=[
            ("hours", "Hours"),
            ("days", "Days"),
            ("years", "Years"),
        ],
        validators=[DataRequired()],
    )
    reason = StringField(
        "Reason",
        validators=[Optional(), Length(max=500)],
    )
    submit = SubmitField("Suspend")


class WarningMessageForm(FlaskForm):
    message = TextAreaField(
        "Creator message",
        validators=[DataRequired(), Length(min=2, max=1000)],
        filters=[lambda value: value.strip() if value else value],
    )
    submit = SubmitField("Send warning")


class AdminActionForm(FlaskForm):
    submit = SubmitField("Confirm")
