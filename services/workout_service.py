from typing import Dict, List
import random
from models import Exercise

# Workout Service

def generate_exercises_list(goal: str, fitness_level: str, equipment: str) -> List[Dict]:
    """
    Generate a professional 10-15 exercise workout routine.
    Structure: Warm-up (2) -> Main (7-11) -> Finisher (1-2) -> Cool-down (1)
    """
    
    # Safety Check
    if not goal:
        goal = "general_fitness"
    
    # 1. Determine Difficulty & Targets
    diff_map = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
    target_difficulty = diff_map.get(fitness_level, "Beginner")
    
    # Target Muscles based on Goal
    primary_muscles = []
    # Map new simplified keys to logic
    if "lose" in goal or "fat_loss" in goal: 
        primary_muscles = ["Full Body", "Legs", "Chest", "Back"]
    elif "gain" in goal or "muscle_gain" in goal: 
        primary_muscles = ["Chest", "Back", "Legs", "Shoulders", "Arms"]
    elif "recomp" in goal or "core" in goal: 
        primary_muscles = ["Full Body", "Abs", "Back"]
    else: 
        primary_muscles = ["Full Body"] # Default
    
    # Equipment Filter
    # If no_equipment, strictly bodyweight. If with_equipment, prefer equipment but allow bodyweight.
    require_equip = (equipment == "with_equipment")
    
    # Helper to fetch by tag/type
    def get_ex(tags, limit, allow_repeat=False, strict_muscle=False):
        query = Exercise.query
        
        # Filter by equipment
        if not require_equip:
            query = query.filter(Exercise.equipment.ilike("%Bodyweight%"))
            
        # Filter by tags (partial match)
        if isinstance(tags, list):
            pass 
        else:
             query = query.filter(Exercise.tags.ilike(f"%{tags}%"))
             
        candidates = query.all()
        
        # Filter strictly by muscle if requested
        if strict_muscle and primary_muscles:
             candidates = [c for c in candidates if any(m.lower() in (c.muscle_group or "").lower() for m in primary_muscles)]
             
        if not candidates: return []
        
        return random.sample(candidates, min(limit, len(candidates)))

    routine = []
    
    # PHASE 1: WARM-UP (2 Exercises)
    # Mobility, Light Cardio
    warmups = get_ex("warmup", 2)
    if not warmups: # Fallback query
        warmups = Exercise.query.filter(Exercise.tags.ilike("%mobility%")).limit(2).all()
    routine.extend([{"phase": "Warm-up", "data": w} for w in warmups])

    # PHASE 2: MAIN LIFT (7-11 Exercises)
    target_count = 10 if fitness_level == "beginner" else (12 if fitness_level == "intermediate" else 15)
    main_count = target_count - 4 # Reserve for other phases
    
    # Query Main Exercises
    main_query = Exercise.query.filter(Exercise.tags.notin_(["warmup", "cooldown", "stretch"]))
    if not require_equip:
         main_query = main_query.filter(Exercise.equipment.ilike("%Bodyweight%"))
    
    # Filter by difficulty approx
    all_main = main_query.all()
    
    # Scoping to muscle groups
    relevant_main = [e for e in all_main if any(m.lower() in (e.muscle_group or "").lower() for m in primary_muscles)]
    if len(relevant_main) < main_count:
        relevant_main = all_main # Fallback to all if not enough specific ones
        
    selected_main = random.sample(relevant_main, min(main_count, len(relevant_main)))
    routine.extend([{"phase": "Main Workout", "data": e} for e in selected_main])
    
    # PHASE 3: FINISHER (1-2 Exercises)
    # HIIT or Core
    finishers = get_ex("hiit", 1) or get_ex("abs", 1)
    routine.extend([{"phase": "Finisher", "data": f} for f in finishers])

    # PHASE 4: COOL-DOWN (1 Exercise)
    cooldowns = get_ex("stretch", 1)
    routine.extend([{"phase": "Cool-down", "data": c} for c in cooldowns])
    
    # Format Result
    formatted_routine = []
    for item in routine:
        ex = item["data"]
        # Smart Sets/Reps
        sets = 3
        reps = "10-12"
        if item["phase"] == "Warm-up": sets=1; reps="60 sec"
        elif item["phase"] == "Main Workout": 
            if "strength" in ex.tags: sets=4; reps="8-10"
            else: sets=3; reps="12-15"
        elif item["phase"] == "Finisher": sets=2; reps="Failure"
        elif item["phase"] == "Cool-down": sets=1; reps="60 sec hold"
        
        formatted_routine.append({
            "name": ex.name,
            "phase": item["phase"],
            "sets": sets,
            "reps": reps,
            "muscle_group": ex.muscle_group,
            "equipment": ex.equipment,
            "difficulty": ex.difficulty,
            "description": ex.description,
            "animation_url": ex.animation_url or "https://assets.lottiefiles.com/packages/lf20_9xRkZk.json",
            "thumbnail_url": ex.thumbnail_url or "https://placehold.co/100x100?text=Ex",
            "id": ex.id
        })
        
    return formatted_routine


def recommend_workout(goal: str, fitness_level: str, freq: int) -> Dict:
    """
    Legacy wrapper retained for compatibility, now uses generate_exercises_list.
    """
    # Simply generate one routine and package it
    # We default to requesting equipment if available in the app context, or just "with_equipment" logic
    exercises = generate_exercises_list(goal, fitness_level, "with_equipment")
    
    return {
        "goal": goal,
        "level": fitness_level,
        "exercises": exercises,
        "estimated_duration": f"{len(exercises) * 3} mins",
        "calories_burn": len(exercises) * 20
    }

def get_equipment_for_workout(exercises: List[Dict]) -> List[str]:
    """Extract required equipment from a list of exercises."""
    equipment = set()
    for ex in exercises:
        eq = ex.get("equipment", "Bodyweight")
        if eq and "Bodyweight" not in eq and "None" not in eq:
            # Clean up string "Dumbbells, Mat" -> ["Dumbbells", "Mat"]
            for item in eq.split(","):
                clean = item.strip()
                if clean: equipment.add(clean)
    return list(equipment)

def recommend_workout_day(goal: str, fitness_level: str, day_index: int, is_break: bool) -> List[Dict]:
    """
    Recommend exercises for a specific day in the plan.
    Rotates muscle groups: Push, Pull, Legs, Core, Full Body.
    """
    if is_break:
        return []

    # Simple rotation based on day index (0-based)
    # 0=Push, 1=Pull, 2=Legs, 3=Core, 4=Full Body
    rotation = ["muscle_gain", "back", "legs", "abs", "fat_loss"]
    day_type = rotation[day_index % len(rotation)]
    
    # Use the robust generation logic which handles phases and volume
    equipment_prio = "with_equipment" # Default to using equipment if available
    
    # We rotate the "goal" parameter slightly to create variety in daily focus,
    # but still respect the user's primary goal in the long run.
    daily_focus = day_type
    if "back" in day_type: daily_focus = "muscle_gain" # Back is muscle
    
    exercises = generate_exercises_list(daily_focus, fitness_level, equipment_prio)
    
    return exercises
