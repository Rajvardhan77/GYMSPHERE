from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "warning")
            return redirect(url_for("auth.register"))
        user = User(
            fullname=request.form.get("fullname"),
            email=email,
            password_hash=generate_password_hash(request.form.get("password")),
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("onboarding.goal"))
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("core.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("core.index"))
