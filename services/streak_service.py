from datetime import datetime, timedelta
from typing import Dict, Optional
from models import User, DailyPlanEntry, UserPlan, db

# Streak Service

def estimate_transformation_days(weight: float, target: float, goal: str) -> int:
    """
    Estimate transformation days using linear regression-style calculation.
    """
    if weight is None or target is None:
        return 0
    
    delta = target - weight
    kg_to_change = abs(delta)
    
    if kg_to_change < 0.1:
        return 0
    
    goal_lower = (goal or "").lower()
    
    # Rate ranges per week (kg/week)
    if goal_lower in ["fat_loss", "lose", "weight_loss"]:
        # Fat loss: 0.4-0.7 kg/week (use average 0.55)
        rate_per_week = 0.55
    elif goal_lower in ["muscle_gain", "gain", "bulk"]:
        # Muscle gain: 0.2-0.4 kg/week (use average 0.3)
        rate_per_week = 0.3
    elif goal_lower in ["recomposition", "recomp"]:
        # Recomposition: slower progression (0.15-0.25 kg/week, use 0.2)
        rate_per_week = 0.2
    else:
        # Default moderate rate
        rate_per_week = 0.4
    
    weeks_needed = kg_to_change / rate_per_week
    days = max(7, int(weeks_needed * 7))
    
    return days

def calculate_streaks(user: User) -> Dict:
    """
    Calculate and update user streaks (Workout & Diet).
    Rules:
    - Workout Streak: Consecutive days of exercise. Rest days count if not missed.
      If missed, streak resets.
    - Diet Streak: Consecutive days of diet completion.
    """
    if not user: return {"workout": 0, "diet": 0}

    # Find active or latest plan
    plan = UserPlan.query.filter_by(user_id=user.id).order_by(UserPlan.created_at.desc()).first()
    if not plan: return {"workout": 0, "diet": 0}
    
    today = datetime.utcnow().date()
    
    # Fetch entries up to yesterday (Streaks are usually built on past completetion)
    # But for "Current Streak" we include today if done.
    
    entries = DailyPlanEntry.query.filter_by(plan_id=plan.id).filter(DailyPlanEntry.date <= today).order_by(DailyPlanEntry.date.desc()).all()
    
    # Calculate Workout Streak
    w_streak = 0
    # Sort entries by date desc (Today -> Past)
    # Filter only relevant days (Exercise days or completed entries)
    # Actually, streak rules: Consecutive days where (Exercise Done OR Rest Day).
    # If today is NOT done yet, it shouldn't break streak from yesterday.
    
    # Check if today is in list
    has_today = False
    if entries and entries[0].date == today:
        has_today = True
        
    start_index = 0
    
    # Special handling for "Today":
    # If Today is DONE -> Streak includes today.
    # If Today is NOT DONE -> Streak is whatever it was yesterday (doesn't reset to 0 unless yesterday was missed).
    
    if has_today:
        e = entries[0]
        today_success = (e.is_exercise_day and e.is_exercise_completed) or (not e.is_exercise_day)
        if today_success:
            w_streak = 1
            start_index = 1
        else:
            # Today not done (or falied), so streak is based on yesterday.
            # But if today is required and failed? (Usually exercise must be done).
            # If not done yet, we ignore today for streak calculation and check yesterday.
            start_index = 1
            pass
            
            
    # Iterate backwards
    for i in range(start_index, len(entries)):
        e = entries[i]
        is_success = (e.is_exercise_day and e.is_exercise_completed) or (not e.is_exercise_day)
        
        # Check continuity (optional, but assumed contiguous for now)
        # If we find a failure, STOP.
        if is_success:
            w_streak += 1
        else:
            break

    # Calculate Diet Streak (simpler: pure consecutive completed days)
    d_streak = 0
    d_start = 0
    if has_today:
        if entries[0].is_diet_completed:
            d_streak = 1
            d_start = 1
        else:
            d_start = 1 # Skip today if not done
            
    for i in range(d_start, len(entries)):
        if entries[i].is_diet_completed:
            d_streak += 1
        else:
            break
            
    # Update User Model
    if w_streak != user.workout_streak or d_streak != user.diet_streak:
        user.workout_streak = w_streak
        user.diet_streak = d_streak
        db.session.commit()
    
    return {"workout": w_streak, "diet": d_streak}

def compute_streaks(user_id: int, plan_id: int) -> Dict:
    """Wrapper for backward compatibility."""
    user = User.query.get(user_id)
    return calculate_streaks(user)
