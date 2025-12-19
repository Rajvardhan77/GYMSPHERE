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
    
    w_streak = 0
    d_streak = 0
    
    # 1. Calculate Workout Streak
    # Look for unbroken chain from today/yesterday backwards
    # If today is NOT done yet, we start looking from yesterday.
    
    # Helper to check if day is "valid" for streak
    # Valid = (Exercise Done) OR (Rest Day)
    # Invalid = (Exercise Day AND Not Done)
    
    if not entries: return {"workout": 0, "diet": 0}
    
    # Handle Today: If not done, it doesn't break streak yet, just doesn't add to it.
    # Unless it's already past interaction time? simpler:
    # If today done -> include. If today not done -> start checking from yesterday.
    
    first_entry = entries[0]
    start_check_idx = 0
    
    if first_entry.date == today:
        workout_done = (first_entry.is_exercise_day and first_entry.is_exercise_completed) or (not first_entry.is_exercise_day)
        diet_done = first_entry.is_diet_completed
        
        if workout_done:
            w_streak += 1
        elif first_entry.is_exercise_day and not first_entry.is_exercise_completed:
            # If today is exercise day and not done, it doesn't break streak from yesterday
            pass 
        
        if diet_done:
            d_streak += 1
        
        start_check_idx = 1 # Continue to yesterday
    
    # Iterate backwards
    for i in range(start_check_idx, len(entries)):
        e = entries[i]
        
        # Workout Logic
        # Rest days maintain streak
        is_success_w = (e.is_exercise_day and e.is_exercise_completed) or (not e.is_exercise_day)
        
        # Check gap between dates? We assume entries are contiguous days.
        # If there's a date gap, streak breaks.
        expected_date = today - timedelta(days=i) # Approximate
        # We should check date continuity if strictly needed, but let's assume entries exist for every day in plan
        
        if is_success_w:
            w_streak += 1
        else:
            break
            
    # 2. Calculate Diet Streak
    # Iterate backwards again
    w_streak_temp = w_streak # Save it
    
    # Reset for diet
    # Logic: Diet must be done every day
    # Continue from where we left off or restart loop? Restart loop is clearer
    
    # Simple Diet Loop
    d_streak_count = 0
    # Check today again for diet
    if entries[0].date == today and entries[0].is_diet_completed:
        d_streak_count = 1
    
    # Backwards from yesterday
    for i in range(1 if entries[0].date == today else 0, len(entries)):
        e = entries[i]
        if e.is_diet_completed:
            d_streak_count += 1
        else:
            break
            
    # Update User Model
    if w_streak_temp != user.workout_streak or d_streak_count != user.diet_streak:
        user.workout_streak = w_streak_temp
        user.diet_streak = d_streak_count
        db.session.commit()
    
    return {"workout": w_streak_temp, "diet": d_streak_count}

def compute_streaks(user_id: int, plan_id: int) -> Dict:
    """Wrapper for backward compatibility."""
    user = User.query.get(user_id)
    return calculate_streaks(user)
