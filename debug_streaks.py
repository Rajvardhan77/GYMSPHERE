from app import create_app
from models import User, UserPlan, DailyPlanEntry, db
from services.streak_service import calculate_streaks
from datetime import datetime

app = create_app()

with app.app_context():
    # Get the user (assuming ID 1 for single user dev env, or the logged in user)
    # We'll print all users to be sure
    users = User.query.all()
    print(f"--- Founds {len(users)} Users ---")
    for user in users:
        print(f"\nUser: {user.fullname} (ID: {user.id})")
        print(f"Stored Streak - Workout: {user.workout_streak}, Diet: {user.diet_streak}")
        print(f"Last Workout Date: {user.last_workout_date}")
        
        # Check Plan
        plan = UserPlan.query.filter_by(user_id=user.id).order_by(UserPlan.created_at.desc()).first()
        if not plan:
            print("No active plan found.")
            continue
            
        print(f"Active Plan ID: {plan.id}")
        
        # Check Today's Entry
        today = datetime.utcnow().date()
        print(f"Today (UTC): {today}")
        
        today_entry = DailyPlanEntry.query.filter_by(plan_id=plan.id, date=today).first()
        if today_entry:
            print(f"Today's Entry Found: {today_entry.id}")
            print(f"  - Is Exercise Day: {today_entry.is_exercise_day}")
            print(f"  - Exercise Completed: {today_entry.is_exercise_completed}")
            print(f"  - Diet Completed: {today_entry.is_diet_completed}")
        else:
            print("NO ENTRY FOUND FOR TODAY!")
            # Check most recent entry
            last_entry = DailyPlanEntry.query.filter_by(plan_id=plan.id).order_by(DailyPlanEntry.date.desc()).first()
            if last_entry:
                print(f"Most recent entry is: {last_entry.date}")
            else:
                print("No entries in plan.")
                
        # Run Calculation Debug
        print("Running Calculation...")
        streaks = calculate_streaks(user)
        print(f"Calculated Streak: {streaks}")
