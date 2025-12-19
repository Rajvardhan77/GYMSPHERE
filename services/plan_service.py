from datetime import datetime, timedelta
from typing import Optional
from models import User, UserPlan, DailyPlanEntry, db
from services.workout_service import recommend_workout_day
from services.diet_service import recommend_meals_for_day, recommend_diet

# Plan Service

def generate_month_plan(user: User, start_date: Optional[str] = None) -> Optional[UserPlan]:
    """
    Generate a 30-day workout and diet plan.
    """
    
    if not start_date:
        start_date_obj = datetime.utcnow().date()
    else:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except:
            start_date_obj = datetime.utcnow().date()

    goal = user.goal or "maintain"
    fitness_level = user.fitness_level or "beginner"
    preference = "nonveg" # Default preference
    
    diet_info = recommend_diet(user.weight_kg, user.target_weight_kg, goal)
    calories = diet_info["calories"]
    macros = diet_info["macros"]

    plan = UserPlan(
        user_id=user.id,
        plan_type="workout+diet",
        goal=goal,
        preference=preference,
        start_date=start_date_obj,
        end_date=start_date_obj + timedelta(days=29),
        frequency_per_week=5,
        fitness_level=fitness_level,
        metadata_json={"total_days": 30}
    )
    
    entries = []
    
    for i in range(30):
        current_date = start_date_obj + timedelta(days=i)
        
        # Rule: Every 3rd day is a Rest Day (Day 3, 6, 9...)
        is_break = ((i + 1) % 3 == 0)
            
        diet_payload = recommend_meals_for_day(calories, macros, preference, goal, i)
        
        exercise_payload = []
        if not is_break:
            exercise_payload = recommend_workout_day(goal, fitness_level, i, is_break)
        
        entry = DailyPlanEntry(
            date=current_date,
            is_exercise_day=not is_break,
            exercise_payload=exercise_payload,
            diet_payload=diet_payload,
            streak_group=1
        )
        entries.append(entry)
    
    plan.daily_entries = entries
    
    db.session.add(plan)
    db.session.commit()
    return plan
