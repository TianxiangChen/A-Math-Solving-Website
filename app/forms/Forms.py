from flask_wtf import Form, validators
from wtforms import StringField, TextAreaField, SubmitField, PasswordField,FileField
from wtforms.validators import required, ValidationError, email, Length
from flask_wtf.file import FileAllowed, FileRequired
from app import db_config


class SignupForm(Form):
    username = StringField("Username", [required("Please enter your username."),
            Length(min=6, max=20, message="Username must be between 6-20 characters")])
    email = StringField("Email", [required("Please enter your email address."),
            email("Please a valid email address.")])
    password = PasswordField('Password', [required("Please enter a password."),
            Length(min=6, max=20, message="Username must be between 6-20 characters")])
    conf_password = PasswordField('Confirm password', [required("Please confirm password."),
            Length(min=6, max=20, message="Username must be between 6-20 characters")])
    submit = SubmitField("Create account")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        validate = True

        if not Form.validate(self):
            validate = False

        user = db_config.get_user(self.username.data.lower())
        if user:
            self.username.errors.append("That username is already taken")
            validate = False

        user = db_config.get_user_by_email(self.email.data.lower())
        if user:
            self.email.errors.append("That email is registered to another user")
            validate = False

        if self.conf_password.data != self.password.data:
            self.password.errors.append("Password entered not identical")
            validate = False

        return validate


class SigninForm(Form):
    username = StringField("Username", [required("Please enter your username.")])
    password = PasswordField('Password', [required("Please enter a password.")])
    submit = SubmitField("Sign In")

    def __int__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = db_config.get_user(self.username.data.lower())

        if user and db_config.user_authenticate(user, password_pt=self.password.data):
            return True
        else:
            self.username.errors.append("Invalid username or password")
            return False

# TODO remove easyupload
class EasyUploadForm(Form):
    userID = StringField("Username", [required("Please enter your username.")])
    password = PasswordField('Password', [required("Please enter a password.")])
    uploadedfile = FileField('File', validators=[FileRequired()])
    submit = SubmitField("Upload")

    def __int__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        return True
