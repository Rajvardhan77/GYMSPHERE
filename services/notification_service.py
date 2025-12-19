from datetime import datetime, timedelta
from typing import Optional
from models import Notification, User, DailyPlanEntry, UserPlan, db
from services.streak_service import calculate_streaks

# Notification Service

def create_notification(user, title, message, type="info", payload=None):
    """Helper to create and commit a notification."""
    try:
        n = Notification(
            user_id=user.id,
            title=title,
            message=message,
            type=type,
            payload_json=payload,
            created_at=datetime.utcnow()
        )
        db.session.add(n)
        db.session.commit()
        return n
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

def check_notifications_engine(user: User) -> None:
    """
    Master function to check and generate all smart notifications.
    Should be called on dashboard load or via background job.
    """
    if not user: return

    # 1. Update & Check Streaks (Core Logic)
    streaks = calculate_streaks(user)
    
    # 2. Tomorrow's Plan (Evening Reminder)
    # Trigger after 6 PM
    if datetime.utcnow().hour >= 18:
        schedule_tomorrow_plan_notification(user)

    # 3. Morning Motivation (Daily)
    schedule_morning_reminder(user)

    # 4. Missed Workout Alert (Yesterday)
    check_missed_workout(user)

    # 5. Weekly Summary (Sunday Evening)
    if datetime.utcnow().weekday() == 6 and datetime.utcnow().hour >= 18:
        generate_weekly_summary(user)


def schedule_tomorrow_plan_notification(user: User):
    """Check tomorrow's plan and notify user."""
    
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    
    # Find active plan
    plan = UserPlan.query.filter(UserPlan.user_id == user.id, UserPlan.end_date >= tomorrow).first()
    if not plan: return

    entry = DailyPlanEntry.query.filter_by(plan_id=plan.id, date=tomorrow).first()
    if not entry: return

    title = "Tomorrow's Plan Ready 📅"
    if Notification.query.filter_by(user_id=user.id, title=title, is_read=False).first():
        return

    if entry.is_exercise_day:
        # Get first 2 exercises
        ex_names = [ex['name'] for ex in (entry.exercise_payload or [])[:2]]
        workout_preview = ", ".join(ex_names)
        msg = f"Tomorrow's Workout: {workout_preview} + more. Get ready!"
    else:
        msg = "Tomorrow is a Rest Day. Focus on recovery and nutrition."
        
    create_notification(user, title, msg, type="plan", payload={"date": str(tomorrow)})


def schedule_morning_reminder(user: User):
    """Daily AI Coach motivation."""
    today = datetime.utcnow().date()
    title = "Coach Update 🤖"
    
    # Only one per day
    if Notification.query.filter(
        Notification.user_id == user.id, 
        Notification.title == title,
        Notification.created_at >= datetime.utcnow().replace(hour=0, minute=0)
    ).first():
        return
    
    msg = get_ai_coach_message(user)
    create_notification(user, title, msg, type="motivation")


def check_missed_workout(user: User):
    """Check if yesterday's workout was missed."""
    
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    
    # active plan covering yesterday
    plan = UserPlan.query.filter(UserPlan.user_id == user.id, UserPlan.start_date <= yesterday).first()
    if not plan: return
    
    entry = DailyPlanEntry.query.filter_by(plan_id=plan.id, date=yesterday).first()
    
    # If it was exercise day, and NOT completed
    if entry and entry.is_exercise_day and not entry.is_exercise_completed:
        title = "Missed Workout ⚠️"
        if not Notification.query.filter_by(user_id=user.id, title=title, created_at=yesterday).first():
             create_notification(user, title, "You missed yesterday's workout. Don't let it break your momentum! Get back on track today.", type="alert")


def get_ai_coach_message(user: User) -> str:
    """Generate rule-based AI coach message."""
    import random
    
    streak = user.workout_streak
    
    if streak > 5:
        return random.choice([
            f"Unstoppable! {streak} day streak. You're building a new version of yourself.",
            "Consistency is your superpower. Keep this streak alive!",
            "You are crushing it. Remember why you started."
        ])
    elif streak > 2:
        return random.choice([
            "Great momentum! Keep pushing.",
            "You're doing great. Stay focused today.",
            "Another day, another opportunity to improve."
        ])
    else:
        return random.choice([
            "The hardest part is showing up. You got this!",
            "Small steps every day lead to big results.",
            "Don't give up. Consistency beats intensity.",
            "Let's make today count!"
        ])


def generate_weekly_summary(user):
    """
    Weekly summary notification.
    """
    # Logic in a future weekly_progress_check function
    # For now, just a stub
    pass
