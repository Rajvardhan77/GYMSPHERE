from app import create_app
from models import User, UserPlan, DailyPlanEntry, db
from services.plan_service import generate_month_plan

app = create_app()

with app.app_context():
    user = User.query.get(3) # 'abcde'
    if not user:
        print("User 3 not found!")
        exit(1)
        
    print(f"Refreshing plan for {user.fullname}...")
    
    # 1. Delete existing plans
    plans = UserPlan.query.filter_by(user_id=user.id).all()
    for p in plans:
        db.session.delete(p)
    db.session.commit()
    print("Deleted old plans.")
    
    # 2. Generate New Plan
    # Ensure defaults
    if not user.goal: user.goal = "muscle_gain"
    if not user.fitness_level: user.fitness_level = "intermediate"
    if not user.freq_per_week: user.freq_per_week = 5
    
    new_plan = generate_month_plan(user)
    print(f"Generated new plan: ID {new_plan.id}")
    
    # 3. Verify Today's Entry
    from datetime import datetime
    today = datetime.utcnow().date()
    entry = DailyPlanEntry.query.filter_by(plan_id=new_plan.id, date=today).first()
    
    if entry:
        print(f"Today's Entry ({today}):")
        print(f"  - Is Exercise Day: {entry.is_exercise_day}")
        if entry.is_exercise_day:
            print(f"  - Exercise Count: {len(entry.exercise_payload)}")
        else:
            print("  - REST DAY")
    else:
        # It's possible the plan starts today but time zones...
        # Let's check the first entry
        first = DailyPlanEntry.query.filter_by(plan_id=new_plan.id).first()
        print(f"First Entry Intent: {first.date} (Is Ex: {first.is_exercise_day})")

    print("Done.")
