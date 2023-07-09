from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, URL, Email, length,Regexp
from flask_ckeditor import CKEditorField


class Login(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email(), length(min=8, max=80)])
    password = PasswordField(label="Password", validators=[DataRequired(), length(min=8, max=50)])
    submit = SubmitField(label="Login")


class Comment(FlaskForm):
    body = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


class Contact(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    phone = StringField(label="Phone", validators=[DataRequired()])
    message = TextAreaField(label="Message", validators=[DataRequired()])
    submit = SubmitField(label="Submit")