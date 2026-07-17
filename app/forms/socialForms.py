from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, URL, ValidationError


IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "webp")


class PostForm(FlaskForm):
    content = TextAreaField(
        "What would you like to share?",
        validators=[Optional(), Length(max=10000)],
        filters=[lambda value: value.strip() if value else None],
    )
    image = FileField(
        "Photo",
        validators=[FileAllowed(IMAGE_EXTENSIONS, "Upload a JPG, PNG, or WebP image.")],
    )
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    submit = SubmitField("Publish post")

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators)
        if (
            not self.content.data
            and not self.image.data
            and not getattr(self, "existing_image", False)
        ):
            self.content.errors.append("Write something or choose a photo.")
            return False
        return valid


class CommentForm(FlaskForm):
    comment_text = StringField(
        "Comment",
        validators=[DataRequired(), Length(max=1000)],
        filters=[lambda value: value.strip() if value else value],
    )
    submit = SubmitField("Comment")


class ProfileSettingsForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=120)],
        filters=[lambda value: value.strip() if value else value],
    )
    profession = StringField(
        "Profession",
        validators=[Optional(), Length(max=100)],
        filters=[lambda value: value.strip() if value else None],
    )
    biography = TextAreaField(
        "Biography",
        validators=[Optional(), Length(max=1000)],
        filters=[lambda value: value.strip() if value else None],
    )
    website_url = StringField(
        "Website",
        validators=[Optional(), Length(max=2048), URL()],
        filters=[lambda value: value.strip() if value else None],
    )
    profile_image = FileField(
        "Profile photo",
        validators=[FileAllowed(IMAGE_EXTENSIONS, "Upload a JPG, PNG, or WebP image.")],
    )
    submit = SubmitField("Save profile")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField(
        "New password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Change password")

    def validate_new_password(self, field):
        if field.data == self.current_password.data:
            raise ValidationError("Choose a password different from your current one.")
