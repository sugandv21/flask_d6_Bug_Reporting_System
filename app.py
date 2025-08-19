import os
from flask import Flask, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Bug
from forms import RegistrationForm, LoginForm, BugForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecret"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "bug_reports.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/home")
@login_required
def home():
    bugs = Bug.query.filter_by(user_id=current_user.id).all()
    last_bug_title = session.get("last_bug_title")
    return render_template("home.html", bugs=bugs, last_bug_title=last_bug_title)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("login"))
        hashed_pw = generate_password_hash(form.password.data, method="pbkdf2:sha256")
        user = User(email=form.email.data, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("Email not registered. Please create an account.", "warning")
            return redirect(url_for("register"))
        if check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid password. Try again.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/add_bug", methods=["GET", "POST"])
@login_required
def add_bug():
    form = BugForm()
    if form.validate_on_submit():
        bug = Bug(title=form.title.data, description=form.description.data, user_id=current_user.id)
        db.session.add(bug)
        db.session.commit()
        session["last_bug_title"] = form.title.data  # store in session
        flash("Bug reported successfully!", "success")
        return redirect(url_for("home"))
    return render_template("add_bug.html", form=form)


if __name__ == "__main__":
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
