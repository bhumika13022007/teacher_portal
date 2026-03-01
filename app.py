from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

login_manager = LoginManager(app)
login_manager.login_view = "login"

bcrypt = Bcrypt(app)

# --------- UPLOAD FOLDER ---------
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------- DATABASE ---------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            photo TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --------- USER CLASS ---------
class User(UserMixin):
    def __init__(self, id_, name, email, password, photo):
        self.id = id_
        self.name = name
        self.email = email
        self.password = password
        self.photo = photo

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(*user)
    return None

# --------- ROUTES ---------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form["name"]
        email=request.form["email"]
        password=bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        conn=sqlite3.connect("database.db")
        c=conn.cursor()

        # check duplicate email
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        if c.fetchone():
            flash("Email already exists. Please login.")
            conn.close()
            return redirect(url_for("login"))

        # default photo
        photo="default.png"

        c.execute(
            "INSERT INTO users(name,email,password,photo) VALUES(?,?,?,?)",
            (name,email,password,photo)
        )
        conn.commit()
        conn.close()

        flash("Registered successfully. Login now.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]

        conn=sqlite3.connect("database.db")
        c=conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user=c.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[3], password):
            login_user(User(*user))
            return redirect(url_for("home"))
        else:
            flash("Invalid login")

    return render_template("login.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/teacher")
@login_required
def teacher():
    return render_template("teacher_space.html")

@app.route("/field")
@login_required
def field():
    return render_template("field_officer_space.html")

# --------- PROFILE ---------
@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    if request.method=="POST":
        file=request.files["photo"]

        if file and file.filename!="":
            filename=secure_filename(file.filename)
            filepath=os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            conn=sqlite3.connect("database.db")
            c=conn.cursor()
            c.execute(
                "UPDATE users SET photo=? WHERE id=?",
                (filename,current_user.id)
            )
            conn.commit()
            conn.close()

            flash("Profile photo updated successfully")

    # get updated user
    conn=sqlite3.connect("database.db")
    c=conn.cursor()
    c.execute("SELECT name,email,photo FROM users WHERE id=?", (current_user.id,))
    user=c.fetchone()
    conn.close()

    return render_template("profile.html", user=user)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# --------- RUN ---------
if __name__=="__main__":
    # create uploads folder automatically
    os.makedirs("static/uploads", exist_ok=True)
    app.run(debug=True)