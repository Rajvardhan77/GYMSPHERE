from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request, flash
from flask_login import current_user, login_required
from models import UserProgress, WaterLog, SleepLog, Product, UserPlan, DailyPlanEntry, db
from services.workout_service import recommend_workout, get_equipment_for_workout
from services.diet_service import recommend_diet, generate_weekly_mealplan
from services.notification_service import check_notifications_engine
from services.streak_service import compute_streaks

core_bp = Blueprint('core', __name__)

@core_bp.route("/intro")
def intro():
    return render_template("intro.html")

@core_bp.route("/_status")
def status():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "GymSphere"})

@core_bp.route("/_health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@core_bp.route("/")
def index():
    if not session.get("intro_shown"):
        session["intro_shown"] = True
        return redirect(url_for("core.intro"))
    return render_template("index.html")

@core_bp.route("/dashboard")
@login_required
def dashboard():
    # Hub Dashboard: Focus on Today + Summary
    workout = None
    diet = None
    chart_labels = []
    chart_values = []
    
    today = datetime.utcnow().date()
    # 0. Fetch Active Plan Entry for Today
    active_plan = UserPlan.query.filter_by(user_id=current_user.id).order_by(UserPlan.created_at.desc()).first()
    today_entry = None
    if active_plan:
            today_entry = DailyPlanEntry.query.filter_by(plan_id=active_plan.id, date=today).first()
            
    try:
        # 1. Today's Workout Snippet
        if today_entry:
            if today_entry.is_exercise_day:
                ex_list = today_entry.exercise_payload or []
                workout = {
                    "frequency": current_user.freq_per_week,
                    "exercises": ex_list[:3] if ex_list else [],
                    "total_exercises": len(ex_list),
                    "duration_min": "45"
                }
                # Keep full workout available for "Start Workout" button context if needed
                full_workout = {"exercises": ex_list} 
            else:
                # Rest Day
                workout = {
                    "frequency": current_user.freq_per_week,
                    "exercises": [],
                    "total_exercises": 0,
                    "duration_min": 0,
                    "is_rest_day": True
                }
                full_workout = {"exercises": []}
        else:
            # Fallback
            full_workout = recommend_workout(current_user.goal, current_user.fitness_level, current_user.freq_per_week or 3)
            workout = {
                "frequency": full_workout.get("frequency"),
                "exercises": full_workout.get("exercises", [])[:3], 
                "total_exercises": len(full_workout.get("exercises", [])),
                "duration_min": "45"
            }

        # 2. Today's Diet Target
        diet = recommend_diet(current_user.weight_kg, current_user.target_weight_kg, current_user.goal)
        
        # 3. Gamification & Streaks (Needed for Dashboard Summary)
        check_notifications_engine(current_user)
        
        # Force recalculate streak to ensure it's up to date (especially after fixes)
        # We need the plan_id.
        latest_plan = UserPlan.query.filter_by(user_id=current_user.id).order_by(UserPlan.created_at.desc()).first()
        if latest_plan:
             compute_streaks(current_user.id, latest_plan.id)
        
        # Refresh user instance to get updated values
        db.session.refresh(current_user)
        
        workout_streak = current_user.workout_streak
        diet_streak = current_user.diet_streak
        
        # 4. Chart Data (Last 7 entries)
        progress_logs = (
            UserProgress.query.filter_by(user_id=current_user.id)
            .order_by(UserProgress.logged_at.desc())
            .limit(7)
            .all()
        )
        # Reverse to show chronological order left-to-right
        progress_logs.reverse()
        chart_labels = [log.logged_at.strftime("%b %d") for log in progress_logs]
        chart_values = [log.weight for log in progress_logs]

    except Exception as e:
        print(f"Dashboard Error: {e}")
        # Fallbacks
        if not workout:
            workout = {"frequency": 3, "exercises": [], "total_exercises": 0, "duration_min": 0}
        if not diet:
            diet = {"calories": 0, "macros": {"protein_g": 0, "carbs_g": 0, "fats_g": 0}}
        workout_streak = current_user.workout_streak or 0
        diet_streak = current_user.diet_streak or 0
        # chart_labels/values already defaulted above

    return render_template(
        "dashboard.html",
        workout=workout,
        diet=diet,
        user=current_user,
        workout_streak=workout_streak,
        diet_streak=diet_streak,
        chart_labels=chart_labels,
        chart_values=chart_values
    )

@core_bp.route("/workout")
@login_required
def workout_page():
    workout = recommend_workout(current_user.goal, current_user.fitness_level, current_user.freq_per_week or 3)
    equipment = get_equipment_for_workout(workout.get("exercises", []))
    return render_template("workout.html", workout=workout, equipment=equipment)

@core_bp.route("/shop")
@login_required
def shop_page():
    return render_template("shopping.html", user=current_user)

@core_bp.route("/diet")
@login_required
def diet_page():
    diet = recommend_diet(current_user.weight_kg, current_user.target_weight_kg, current_user.goal)
    mealplan = generate_weekly_mealplan(diet or {}, current_user.goal)
    return render_template("diet.html", diet=diet, mealplan=mealplan)

@core_bp.route("/progress")
@login_required
def progress_page():
    # Fetch detailed progress data
    progress_logs = (
        UserProgress.query.filter_by(user_id=current_user.id)
        .order_by(UserProgress.logged_at.asc())
        .all()
    )
    progress_labels = [log.logged_at.strftime("%Y-%m-%d") for log in progress_logs]
    progress_values = [log.weight for log in progress_logs]
    
    # 2. Lifestyle Data (Moved from Dashboard)
    today_date = datetime.utcnow().date()
    water_logs = WaterLog.query.filter(
        WaterLog.user_id == current_user.id,
        WaterLog.date == today_date
    ).all()
    hydration_current = sum(log.amount_ml for log in water_logs)
    hydration_goal = 3000 
    
    sleep_log = SleepLog.query.filter(
        SleepLog.user_id == current_user.id,
        SleepLog.date == today_date
    ).first()
    sleep_data = {"hours": sleep_log.hours if sleep_log else 0, "quality": sleep_log.quality if sleep_log else "-"}

    # 3. Calendar Check-In History
    from models import UserPlan, DailyPlanEntry
    active_plan = UserPlan.query.filter_by(user_id=current_user.id).order_by(UserPlan.created_at.desc()).first()
    calendar_entries = []
    if active_plan:
        calendar_entries = DailyPlanEntry.query.filter_by(plan_id=active_plan.id).order_by(DailyPlanEntry.date.asc()).all()
    
    return render_template(
        "progress.html", 
        progress_labels=progress_labels, 
        progress_values=progress_values,
        hydration_data={"current": hydration_current, "goal": hydration_goal},
        sleep_data=sleep_data,
        calendar_entries=calendar_entries,
        now_date=today_date
    )

@core_bp.route("/account")
@login_required
def account_page():
    user_badges = [ub.badge for ub in current_user.badges]
    return render_template("account.html", user=current_user, badges=user_badges)

@core_bp.route("/update_progress", methods=["POST"])
@login_required
def update_progress():
    weight = request.form.get("weight")
    if weight:
        entry = UserProgress(user_id=current_user.id, weight=float(weight), logged_at=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
    return redirect(url_for("core.progress_page"))

@core_bp.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash("Admin access required", "warning")
        return redirect(url_for("core.dashboard"))
    from models import DietPlan, Exercise
    exercises = Exercise.query.all()
    diet_plans = DietPlan.query.all()
    products = Product.query.all()
    return render_template(
        "admin.html",
        exercises=exercises,
        diet_plans=diet_plans,
        products=products,
    )
