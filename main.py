from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE IN DB
class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get('email')
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            #User alreay exists
            flash("You've already signed up with that email, Login Instead!")
            return redirect(url_for('login'))
        password_hashed = generate_password_hash(request.form.get('password'), 'pbkdf2', 8)
        new_user = User(name=request.form.get('name'), email=email, password=password_hashed)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Logged in successfully.')
        return redirect(url_for('secrets'))
    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email, password = request.form.get('email'), request.form.get('password')
        found_user = db.session.execute(db.select(User).where(User.email==email)).scalar()
        # password_hashed = generate_password_hash(password, 'pbkdf2', 8)
        if found_user and check_password_hash(found_user.password, password):
            login_user(found_user)
            flash('Logged in successfully.')
            return redirect(url_for('secrets'))
        else:
            flash("Login Failed, invalid email or password")
            return redirect(url_for('login'))
    return render_template("login.html")


@app.route('/secrets')
def secrets():
    if current_user.is_authenticated:
        return render_template("secrets.html", name=current_user.name)
    else:
        flash("You must login first")
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have logged out successfully!")
    return redirect(url_for('home'))


@app.route('/download')
@login_required
def download():
    return send_from_directory('static', path='files/cheat_sheet.pdf')


if __name__ == "__main__":
    app.run(debug=True)
