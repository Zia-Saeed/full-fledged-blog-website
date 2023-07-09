from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, length


class Register(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email(), length(min=8, max=80)])
    password = PasswordField(label="Password", validators=[DataRequired(), length(min=8)])
    name = StringField(label="Name", validators=[DataRequired(), length(min=3)])
    submit = SubmitField(label="Sign Me up!")