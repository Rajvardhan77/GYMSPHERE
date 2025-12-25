from typing import Dict, Any
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from models import db

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route("/goal", methods=["GET", "POST"])
def goal():
    if request.method == "POST" and current_user.is_authenticated:
        current_user.goal = request.form.get("goal")
        db.session.commit()
        return redirect(url_for("onboarding.body_type"))
    return render_template("goal_select.html")

@onboarding_bp.route("/body-type", methods=["GET", "POST"])
def body_type():
    if request.method == "POST" and current_user.is_authenticated:
        current_user.body_level = request.form.get("body_type")
        db.session.commit()
        return redirect(url_for("onboarding.measurements"))
    return render_template("body_type.html")

@onboarding_bp.route("/measurements", methods=["GET", "POST"])
def measurements():
    if request.method == "POST" and current_user.is_authenticated:
        current_user.height_cm = request.form.get("height_cm") or current_user.height_cm
        current_user.weight_kg = request.form.get("weight_kg") or current_user.weight_kg
        current_user.target_weight_kg = request.form.get("target_weight_kg") or current_user.target_weight_kg
        db.session.commit()
        return redirect(url_for("onboarding.activity"))
    return render_template("measurements.html")

@onboarding_bp.route("/activity", methods=["GET", "POST"])
def activity():
    if request.method == "POST" and current_user.is_authenticated:
        current_user.activity_level = request.form.get("activity_level")
        current_user.freq_per_week = request.form.get("freq_per_week") or current_user.freq_per_week
        db.session.commit()
        return redirect(url_for("onboarding.fitness_level"))
    return render_template("activity.html")

from services.plan_service import generate_month_plan

@onboarding_bp.route("/fitness-level", methods=["GET", "POST"])
def fitness_level():
    if request.method == "POST" and current_user.is_authenticated:
        current_user.fitness_level = request.form.get("fitness_level")
        db.session.commit()
        
        # Generate 30-Day Premium Plan
        generate_month_plan(current_user)
        
        return redirect(url_for("core.dashboard"))
    return render_template("fitness_level.html")

@onboarding_bp.route("/api/onboard", methods=["POST"])
@login_required
def api_onboard():
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
    for field in [
        "goal",
        "body_level",
        "activity_level",
        "fitness_level",
    ]:
        if field in data:
            setattr(current_user, field, data[field])
    for field in ["height_cm", "weight_kg", "target_weight_kg", "freq_per_week"]:
        if field in data:
            setattr(current_user, field, data[field])
    db.session.commit()
    return jsonify({"status": "ok"})
