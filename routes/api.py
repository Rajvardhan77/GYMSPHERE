from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from flask import current_app
from models import UserPlan, DailyPlanEntry, UserCheckIn, Notification, WaterLog, SleepLog, User, UserProgress, db
from services.plan_service import generate_month_plan
from services.streak_service import compute_streaks
from services.notification_service import schedule_tomorrow_plan_notification 
from services.diet_service import recommend_shopping

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route("/plan/generate", methods=["POST"])
@login_required
def api_plan_generate():
    data = request.get_json(force=True, silent=True) or {}
    start_date = data.get("start_date")
    
    plan = generate_month_plan(current_user, start_date)
    
    return jsonify({
        "status": "ok",
        "plan_id": plan.id,
        "message": "Plan generated successfully"
    })

@api_bp.route("/plan/today")
@login_required
def api_plan_today():
    today = datetime.utcnow().date()
    
    # Find active plan (end date >= today)
    plan = UserPlan.query.filter(
        UserPlan.user_id == current_user.id,
        UserPlan.end_date >= today
    ).order_by(UserPlan.created_at.desc()).first()
    
    if not plan:
        return jsonify({"status": "no_plan"})
        
    entry = DailyPlanEntry.query.filter_by(plan_id=plan.id, date=today).first()
    if not entry:
            return jsonify({"status": "no_entry_for_today"})
            
    return jsonify({
        "status": "ok",
        "entry": {
            "id": entry.id,
            "date": entry.date.isoformat(),
            "is_exercise_day": entry.is_exercise_day,
            "is_exercise_completed": entry.is_exercise_completed,
            "is_diet_completed": entry.is_diet_completed,
            "exercise_payload": entry.exercise_payload,
            "diet_payload": entry.diet_payload
        }
    })

@api_bp.route("/plan/checkin", methods=["POST"])
@login_required
def api_plan_checkin():
    # We need to manually import schedule_next_day_notifications if it wasn't migrated?
    # Actually wait, `schedule_next_day_notifications` was in `utils.py`? 
    # I saw `schedule_tomorrow_plan_notification` in `notification_service`.
    # Let's check imports in `utils.py` previously... 
    # The original code called `utils.schedule_next_day_notifications`.
    # But in my read of `utils.py`, I saw `schedule_tomorrow_plan_notification`.
    # Maybe I missed a rename? Or it was an alias?
    # Checking `utils.py` (Step 58): line 589 is `schedule_tomorrow_plan_notification`
    # Checking `app.py` (Step 59): line 380 `from utils import schedule_next_day_notifications`
    # Something is mismatching. `utils.py` line 380 called `schedule_next_day_notifications`.
    # But `utils.py` line 589 define `schedule_tomorrow_plan_notification`.
    # I'll use `schedule_tomorrow_plan_notification` which I migrated.
    
    data = request.get_json()
    entry_id = data.get("entry_id")
    checkin_type = data.get("type") # exercise, diet
    
    entry = DailyPlanEntry.query.get_or_404(entry_id)
    if entry.plan.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    # Update status and last check-in date
    if checkin_type == "exercise":
        entry.is_exercise_completed = True
        entry.exercise_completed_at = datetime.utcnow()
        current_user.last_workout_date = datetime.utcnow().date()
    elif checkin_type == "diet":
        entry.is_diet_completed = True
        entry.diet_completed_at = datetime.utcnow()
        current_user.last_diet_date = datetime.utcnow().date()
        
    # Log check-in
    checkin = UserCheckIn(
        user_id=current_user.id,
        daily_entry_id=entry.id,
        type=checkin_type,
        note=data.get("note")
    )
    db.session.add(checkin)
    db.session.commit()
    
    # Trigger updates
    schedule_tomorrow_plan_notification(current_user)
    streaks = compute_streaks(current_user.id, entry.plan_id)
    
    return jsonify({
        "status": "ok",
        "streaks": streaks
    })

@api_bp.route("/plan/calendar")
@login_required
def api_plan_calendar():
    # Get active plan
    today = datetime.utcnow().date()
    plan = UserPlan.query.filter(
        UserPlan.user_id == current_user.id
    ).order_by(UserPlan.created_at.desc()).first()
    
    if not plan:
            return jsonify([])
            
    entries = DailyPlanEntry.query.filter_by(plan_id=plan.id).all()
    
    result = []
    for e in entries:
        # Determine status color/state for frontend
        status = "future"
        if e.date < today:
            if (e.is_exercise_day and e.is_exercise_completed and e.is_diet_completed) or \
                (not e.is_exercise_day and e.is_diet_completed):
                status = "completed"
            else:
                status = "missed"
        elif e.date == today:
             if (e.is_exercise_day and e.is_exercise_completed and e.is_diet_completed) or \
                (not e.is_exercise_day and e.is_diet_completed):
                 status = "completed"
             else:
                 status = "today"
        
        result.append({
            "date": e.date.isoformat(),
            "is_exercise_day": e.is_exercise_day,
            "is_exercise_completed": e.is_exercise_completed,
            "is_diet_completed": e.is_diet_completed,
            "status": status
        })
        
    return jsonify(result)

@api_bp.route("/plan/stats")
@login_required
def api_plan_stats():
    today = datetime.utcnow().date()
    plan = UserPlan.query.filter(
        UserPlan.user_id == current_user.id,
        UserPlan.end_date >= today
    ).order_by(UserPlan.created_at.desc()).first()
    
    if not plan:
        return jsonify({"current_streak": 0, "longest_streak": 0})
        
    streaks = compute_streaks(current_user.id, plan.id)
    return jsonify(streaks)

@api_bp.route("/notifications")
@login_required
def api_notifications():
    # Unread first, then recent read
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.is_read.asc(),
        Notification.created_at.desc()
    ).limit(20).all()
    
    return jsonify([{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "is_read": n.is_read,
        "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
        "payload": n.payload_json
    } for n in notifs])

@api_bp.route("/notifications/read", methods=["POST"])
@login_required
def api_notifications_read():
    data = request.get_json(silent=True) or {}
    notif_id = data.get("id")
    
    if notif_id:
        n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
        if n:
            n.is_read = True
            db.session.commit()
    else:
        # Mark all as read
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
        db.session.commit()
        
    return jsonify({"status": "ok"})

@api_bp.route("/shop/recommend")
@login_required
def api_shop_recommend():
    items = recommend_shopping(current_user.goal, current_app)
    return jsonify(items)

@api_bp.route("/water/log", methods=["POST"])
@login_required
def api_water_log():
    data = request.get_json(silent=True) or {}
    amount = data.get("amount", 250)
    
    log = WaterLog(user_id=current_user.id, amount_ml=amount, date=datetime.utcnow().date())
    db.session.add(log)
    db.session.commit()
    
    return jsonify({"status": "ok", "added": amount})

@api_bp.route("/sleep/log", methods=["POST"])
@login_required
def api_sleep_log():
    data = request.get_json(silent=True) or {}
    hours = data.get("hours", 8)
    quality = data.get("quality", "Good")
    
    log = SleepLog(user_id=current_user.id, hours=hours, quality=quality, date=datetime.utcnow().date())
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "ok"})

@api_bp.route("/leaderboard")
@login_required
def api_leaderboard():
    # Mock leaderboard
    top_users = db.session.query(
        User.fullname, db.func.count(UserProgress.id).label('score')
    ).join(UserProgress).group_by(User.id).order_by(db.desc('score')).limit(5).all()
    
    leaderboard = [{"name": u.fullname, "score": u.score, "metric": "Check-ins"} for u in top_users]
    
    if not leaderboard:
        leaderboard = [{"name": "Admin User", "score": 42, "metric": "Workouts"}, {"name": "Bot One", "score": 30, "metric": "Workouts"}]
        
    return jsonify(leaderboard)
