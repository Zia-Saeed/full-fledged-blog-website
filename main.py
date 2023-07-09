from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm
from flask_gravatar import Gravatar
from register_form import Register
from login_form import Login, Comment, Contact
from functools import wraps
import smtplib
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)


login_manager = LoginManager()
login_manager.__init__(app=app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CONFIGURE TABLES


# Database Table users.
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False,)
    name = db.Column(db.String(250), nullable=False, unique=True)
    # Post is object of BlogPost and can give all the values of columns of BlogPost
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")


# Database Table blog_posts.
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("Users", back_populates="posts")
    # author is the Object of Users and can give all the values of columns of Users
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # Parent relation
    comments = relationship("Comments", back_populates="parent_post")


# Database Table comments.
class Comments(db.Model, UserMixin):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    comment_author = relationship("Users", back_populates="comments")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # child relation
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text(1000), nullable=False)
# db.create_all()


# creating user session.
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


# function for home page.
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()

    return render_template("index.html", all_posts=posts)


# registration of user.
@app.route('/register', methods=["POST", "GET"])
def register():
    form = Register()
    if request.method == "POST" and form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        name = Users.query.filter_by(name=form.name.data).first()
        if user:
            flash("You have already signed up with this email,Instead Login.")
            return redirect(url_for("login"))
        if name:
            flash("This Username is already taken, user another name.")
            return render_template("register.html", form=form)
        password = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        new_user =Users(
            email = form.email.data,
            password = password,
            name = form.name.data,
            )
        db.session.add(new_user)
        db.session.commit()



        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

# login of user.
@app.route('/login', methods=["POST", "GET"])
def login():
    form = Login()
    if request.method == "POST" and form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(password=form.password.data, pwhash=user.password):
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                flash("Incorrect password.")
                return render_template("login.html", form=form)
        else:
            flash("Email does not exit.")
            return render_template("login.html", form=form)
    return render_template("login.html", form=form)


# disband the user session.
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


"""Decorator function for admin authentication."""
def admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return func(*args, **kwargs)
    return wrapper


# It will show the particular blog post.
@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    form = Comment()
    gravatar = Gravatar(
        app,
        size=100,
        rating='g',
        default='retro',
        force_default=False,
        force_lower=False,
        use_ssl=False,
        base_url=None
    )
    requested_post = BlogPost.query.get(post_id)
    if request.method == "POST" and form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("To comment on a blog, You need to Login or Register your account.")
            return redirect(url_for("login"))

        new_comment = Comments(
            text = form.body.data,
            author_id = current_user.id,
            post_id=post_id,
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))
    return render_template("post.html", post=requested_post, comment=form, gravatar=gravatar)


# display about.html file.
@app.route("/about")
def about():
    return render_template("about.html")


# Function for contacting the website owner through sending the mail.
@app.route("/contact", methods=["POST", "GET"])
def contact():
    contact_form = Contact()
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("To contact please Login or Register")
            return redirect(url_for('register'))
        if contact_form.validate_on_submit() and current_user.is_authenticated:
            name = contact_form.name.data
            email = contact_form.email.data
            phone = contact_form.phone.data
            message = contact_form.message.data
            with smtplib.SMTP("smtp.gmail.com") as connection:
                app_password = os.environ.get("app_password")
                admin = "zia.aseh@gmail.com"
                connection.starttls()
                connection.login(
                    user=admin,
                    password=app_password
                )
                connection.sendmail(
                    from_addr=admin,
                    to_addrs=admin,
                    msg=f"Subject:Client\n\nname: {name}\nemail: {email}\nphone: {phone}\nmessage: {message}")
                flash("Message send Successfully")
                return redirect(url_for("contact"))
    return render_template("contact.html", form=contact_form)


# function for adding a new blog post can be done by admin only.
@app.route("/new-post", methods=["POST", "GET"])
@login_required
@admin
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit() and request.method == "POST":
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

# function for editing the blogs.For admin use only.
@app.route("/edit-post/<int:post_id>", methods=["POST", "GET"])
@login_required
@admin
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit() and request.method == "POST":
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)

# function for deleting the Blogs.For admin use only.
@app.route("/delete/<int:post_id>")
@login_required
@admin
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)




