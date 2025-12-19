from typing import Dict, List
from models import Product

# Diet Service

def recommend_diet(weight: float, target: float, goal: str) -> Dict:
    """
    Recommend diet plan using Mifflin-St Jeor-like calculation.
    """
    if weight is None or weight <= 0:
        weight = 70  # Default fallback
    
    goal_lower = (goal or "").lower()
    
    # Simplified Mifflin-St Jeor BMR estimation (using average values)
    # BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age + 5 (male) or -161 (female)
    # Using simplified: BMR ≈ weight * 22 (rough estimate for average person)
    base_bmr = weight * 22
    
    # Activity multiplier (assuming moderate activity)
    activity_multiplier = 1.55
    maintenance_calories = base_bmr * activity_multiplier
    
    # Adjust calories based on goal
    if goal_lower in ["fat_loss", "lose", "weight_loss"]:
        calories = maintenance_calories - 400  # Deficit for fat loss
    elif goal_lower in ["muscle_gain", "gain", "bulk"]:
        calories = maintenance_calories + 300  # Surplus for muscle gain
    elif goal_lower in ["recomposition", "recomp"]:
        calories = maintenance_calories - 100  # Slight deficit for recomposition
    else:
        calories = maintenance_calories
    
    # Macro calculations
    # Protein: 1.8-2.2g per kg bodyweight (use 2.0g for muscle gain, 1.8g otherwise)
    if goal_lower in ["muscle_gain", "gain", "bulk"]:
        protein_g = weight * 2.0
    else:
        protein_g = weight * 1.8
    
    # Fats: 0.8-1.0g per kg (use 1.0g for muscle gain, 0.8g for fat loss)
    if goal_lower in ["muscle_gain", "gain", "bulk"]:
        fats_g = weight * 1.0
    elif goal_lower in ["fat_loss", "lose", "weight_loss"]:
        fats_g = weight * 0.7  # Lower fat for fat loss
    else:
        fats_g = weight * 0.8
    
    # Carbs: remaining calories
    protein_cals = protein_g * 4
    fats_cals = fats_g * 9
    remaining_cals = calories - protein_cals - fats_cals
    carbs_g = max(0, remaining_cals / 4)
    
    # Generate summary
    goal_display = goal_lower.replace("_", " ").title() if goal_lower else "Balance"
    summary = (
        f"Daily target: {round(calories)} kcal to support {goal_display}. "
        f"Macros: {round(protein_g)}g protein, {round(carbs_g)}g carbs, {round(fats_g)}g fats. "
        f"Focus on {'high protein and carbs' if 'gain' in goal_lower else 'protein and controlled carbs' if 'lose' in goal_lower else 'balanced macros'}."
    )
    
    return {
        "calories": round(calories),
        "macros": {
            "protein_g": round(protein_g),
            "carbs_g": round(carbs_g),
            "fats_g": round(fats_g),
        },
        "summary": summary
    }


def generate_weekly_mealplan(diet: Dict, goal: str) -> List[Dict]:
    """
    Generate 7-day meal plan with breakfast, lunch, dinner, and snacks.
    """
    calories = diet.get("calories", 2000)
    protein_g = diet.get("macros", {}).get("protein_g", 120)
    carbs_g = diet.get("macros", {}).get("carbs_g", 200)
    fats_g = diet.get("macros", {}).get("fats_g", 70)
    
    goal_lower = (goal or "").lower()
    
    # Meal templates adjusted by goal
    if goal_lower in ["fat_loss", "lose", "weight_loss"]:
        # High protein, lower carb, clean foods
        meal_templates = [
            {
                "breakfast": "Greek yogurt with berries and almonds",
                "lunch": "Grilled chicken salad with olive oil dressing",
                "dinner": "Baked salmon with steamed vegetables",
                "snacks": "Protein shake, apple with peanut butter"
            },
            {
                "breakfast": "Scrambled eggs with spinach and whole grain toast",
                "lunch": "Turkey wrap with vegetables",
                "dinner": "Lean beef stir-fry with broccoli",
                "snacks": "Cottage cheese, mixed nuts"
            },
            {
                "breakfast": "Protein smoothie with banana and spinach",
                "lunch": "Tuna salad with mixed greens",
                "dinner": "Grilled chicken breast with quinoa and asparagus",
                "snacks": "Hard-boiled eggs, cucumber slices"
            },
            {
                "breakfast": "Oatmeal with protein powder and berries",
                "lunch": "Chicken and vegetable soup",
                "dinner": "Baked cod with sweet potato and green beans",
                "snacks": "Greek yogurt, almonds"
            },
            {
                "breakfast": "Egg white omelet with vegetables",
                "lunch": "Grilled chicken Caesar salad (light dressing)",
                "dinner": "Lean pork tenderloin with roasted vegetables",
                "snacks": "Protein bar, apple"
            },
            {
                "breakfast": "Cottage cheese with fruit and nuts",
                "lunch": "Salmon and quinoa bowl",
                "dinner": "Turkey meatballs with zucchini noodles",
                "snacks": "Protein shake, mixed berries"
            },
            {
                "breakfast": "Whole grain toast with avocado and poached eggs",
                "lunch": "Chicken and vegetable stir-fry",
                "dinner": "Grilled fish with brown rice and vegetables",
                "snacks": "Greek yogurt, trail mix"
            }
        ]
    elif goal_lower in ["muscle_gain", "gain", "bulk"]:
        # High protein, high carbs, calorie-dense foods
        meal_templates = [
            {
                "breakfast": "Oatmeal with protein powder, banana, and peanut butter",
                "lunch": "Chicken breast with rice and vegetables",
                "dinner": "Beef steak with potatoes and mixed vegetables",
                "snacks": "Protein shake, granola bar, nuts"
            },
            {
                "breakfast": "Scrambled eggs with bacon and whole grain toast",
                "lunch": "Pasta with ground turkey and marinara sauce",
                "dinner": "Salmon with sweet potato and broccoli",
                "snacks": "Greek yogurt with honey, protein bar"
            },
            {
                "breakfast": "Protein pancakes with syrup and berries",
                "lunch": "Chicken and rice bowl with avocado",
                "dinner": "Pork chops with mashed potatoes and green beans",
                "snacks": "Protein shake, banana, peanut butter"
            },
            {
                "breakfast": "Breakfast burrito with eggs, cheese, and sausage",
                "lunch": "Beef and rice stir-fry",
                "dinner": "Grilled chicken with pasta and vegetables",
                "snacks": "Trail mix, protein shake"
            },
            {
                "breakfast": "Greek yogurt parfait with granola and fruit",
                "lunch": "Turkey sandwich with whole grain bread",
                "dinner": "Baked cod with rice and vegetables",
                "snacks": "Protein bar, mixed nuts, apple"
            },
            {
                "breakfast": "Omelet with cheese, vegetables, and toast",
                "lunch": "Chicken and quinoa bowl",
                "dinner": "Lean beef with potatoes and asparagus",
                "snacks": "Protein shake, Greek yogurt, berries"
            },
            {
                "breakfast": "Protein smoothie bowl with toppings",
                "lunch": "Salmon with rice and vegetables",
                "dinner": "Pork tenderloin with sweet potato and broccoli",
                "snacks": "Protein bar, trail mix, banana"
            }
        ]
    else:  # recomposition or balanced
        # Balanced macros, clean foods
        meal_templates = [
            {
                "breakfast": "Greek yogurt with berries and granola",
                "lunch": "Grilled chicken with quinoa and vegetables",
                "dinner": "Baked salmon with sweet potato and greens",
                "snacks": "Protein shake, mixed nuts"
            },
            {
                "breakfast": "Scrambled eggs with whole grain toast and avocado",
                "lunch": "Turkey and vegetable wrap",
                "dinner": "Lean beef with brown rice and broccoli",
                "snacks": "Greek yogurt, apple"
            },
            {
                "breakfast": "Oatmeal with protein powder and fruit",
                "lunch": "Chicken salad with olive oil dressing",
                "dinner": "Grilled fish with quinoa and vegetables",
                "snacks": "Cottage cheese, almonds"
            },
            {
                "breakfast": "Protein smoothie with spinach and banana",
                "lunch": "Salmon and rice bowl",
                "dinner": "Chicken breast with sweet potato and asparagus",
                "snacks": "Hard-boiled eggs, mixed berries"
            },
            {
                "breakfast": "Whole grain toast with eggs and vegetables",
                "lunch": "Tuna salad with mixed greens",
                "dinner": "Pork tenderloin with brown rice and green beans",
                "snacks": "Protein bar, Greek yogurt"
            },
            {
                "breakfast": "Cottage cheese with fruit and nuts",
                "lunch": "Chicken and vegetable stir-fry",
                "dinner": "Baked cod with quinoa and vegetables",
                "snacks": "Protein shake, trail mix"
            },
            {
                "breakfast": "Egg white omelet with vegetables and cheese",
                "lunch": "Grilled chicken Caesar salad",
                "dinner": "Lean beef with potatoes and mixed vegetables",
                "snacks": "Greek yogurt, protein bar"
            }
        ]
    
    # Generate 7-day plan
    weekly_plan = []
    for day_num in range(7):
        day_plan = meal_templates[day_num % len(meal_templates)]
        weekly_plan.append({
            "day": day_num + 1,
            "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_num],
            "calories": round(calories),
            "macros": {
                "protein_g": round(protein_g),
                "carbs_g": round(carbs_g),
                "fats_g": round(fats_g),
            },
            "meals": {
                "breakfast": day_plan["breakfast"],
                "lunch": day_plan["lunch"],
                "dinner": day_plan["dinner"],
                "snacks": day_plan["snacks"]
            }
        })
    
    return weekly_plan


def recommend_shopping(goal: str, app=None) -> List[Dict]:
    """
    Recommend shopping products based on goal with smart affiliate links.
    """
    goal_lower = (goal or "").lower()
    
    # Goal to equipment/supplements mapping
    recommendations_map = {
        "fat_loss": ["skipping_rope", "resistance_bands", "yoga_mat", "whey_isolate", "smart_watch"],
        "muscle_gain": ["dumbbells", "creatine", "whey_protein", "weight_bench", "lifting_straps"],
        "body_recomp": ["adjustable_dumbbells", "yoga_mat", "protein_powder", "kettlebell"],
        "core_strength": ["ab_wheel", "sliders", "yoga_mat", "medicine_ball"],
        "flexibility": ["yoga_mat", "foam_roller", "yoga_blocks"]
    }
    
    # Default to full body / general
    target_items = recommendations_map.get(goal_lower, ["resistance_bands", "dumbbells", "yoga_mat", "water_bottle"])
    
    products_list = []
    
    # 1. Try DB matches first
    if app:
        try:
            with app.app_context():
                # Simple logic: partial name match or category match
                # For production, we'd have a tag system
                for item_key in target_items:
                    # Search by name similar to item key
                    match = Product.query.filter(Product.name.ilike(f"%{item_key.replace('_', ' ')}%")).first()
                    if match:
                        products_list.append({
                            "id": match.id,
                            "name": match.name,
                            "price": float(match.price),
                            "image_url": match.image_url or "https://placehold.co/200x200?text=GymSphere",
                            "rating": match.rating or 4.5,
                            "src": match.src or "local",
                            "affiliate_url": match.affiliate_url or "#"
                        })
        except Exception:
            pass
            
    # 2. Fill gaps with "Smart" defaults (Affiliate Placeholders)
    # If we didn't find enough items in DB, we generate them dynamically
    
    defaults_db = {
        "skipping_rope": {"name": "Pro Speed Rope", "price": 14.99, "img": "https://m.media-amazon.com/images/I/71q+9gE-cAL._AC_SX679_.jpg"},
        "resistance_bands": {"name": "Heavy Duty Bands Set", "price": 29.99, "img": "https://m.media-amazon.com/images/I/71D0-l-rMzL._AC_SX679_.jpg"},
        "yoga_mat": {"name": "Non-Slip Yoga Mat", "price": 45.00, "img": "https://m.media-amazon.com/images/I/81+6iM6C5XL._AC_SX679_.jpg"},
        "whey_isolate": {"name": "Gold Standard Whey", "price": 69.99, "img": "https://m.media-amazon.com/images/I/71+6P+H6+pL._AC_SX679_.jpg"},
        "smart_watch": {"name": "Fitness Tracker Pro", "price": 129.99, "img": "https://m.media-amazon.com/images/I/61s+N0+1sWL._AC_SX679_.jpg"},
        "dumbbells": {"name": "Hex Dumbbell Pair (10kg)", "price": 59.99, "img": "https://m.media-amazon.com/images/I/71ShRz-BcxL._AC_SX679_.jpg"},
        "creatine": {"name": "Micronized Creatine", "price": 24.99, "img": "https://m.media-amazon.com/images/I/71t+vO-4KqL._AC_SX679_.jpg"},
        "ab_wheel": {"name": "Core Roller", "price": 19.99, "img": "https://m.media-amazon.com/images/I/71-Wl6+FmTL._AC_SX679_.jpg"},
        "adjustable_dumbbells": {"name": "SelectTech Dumbbells", "price": 299.00, "img": "https://m.media-amazon.com/images/I/71+pOdQ7iKL._AC_SX679_.jpg"}
    }
    
    needed = 5 - len(products_list)
    if needed > 0:
        for item_key in target_items:
            if len(products_list) >= 6: break
            
            # If not already present
            if not any(p['name'].lower() in item_key.replace('_', ' ') for p in products_list):
                def_item = defaults_db.get(item_key, {"name": item_key.replace('_', ' ').title(), "price": 25.00, "img": ""})
                
                # Generate valid Amazon Search Link
                search_term = def_item["name"].replace(" ", "+")
                link = f"https://www.amazon.com/s?k={search_term}&tag=gymsphere-20"
                
                products_list.append({
                    "id": None,
                    "name": def_item["name"],
                    "price": def_item["price"],
                    "image_url": def_item["img"] or "https://placehold.co/200x200?text=Product",
                    "rating": 4.8,
                    "src": "amazon",
                    "affiliate_url": link
                })
                
    return products_list


def recommend_meals_for_day(calories: int, macros: Dict, preference: str, goal: str, day_index: int) -> Dict:
    """
    Generate a full day of eating based on calories/macros and preferences.
    """
    # Base templates
    is_nonveg = preference == "nonveg" or preference == "mixed"
    
    # Helper to generate meal string
    def get_meal(type_name):
        base = ""
        if type_name == "breakfast":
            if is_nonveg and goal == "muscle_gain":
                base = "Omelette with spinach & turkey bacon, oatmeal"
            else:
                base = "Greek yogurt parfait with berries & granola"
        elif type_name == "lunch":
            if is_nonveg:
                base = "Grilled chicken breast, quinoa, roasted veggies"
            else:
                base = "Lentil soup, brown rice, avocado salad"
        elif type_name == "dinner":
            if is_nonveg:
                base = "Baked salmon/fish, sweet potato, steamed broccoli"
            else:
                base = "Tofu stir-fry with mixed vegetables"
        elif type_name == "snacks":
            base = "Protein shake, almonds, apple"
        
        variations = [" (Option A)", " (Option B)", " (Spicy)", " (Herbal)"]
        return base + variations[day_index % 4]

    return {
        "calories": calories,
        "protein_g": macros.get("protein_g"),
        "carbs_g": macros.get("carbs_g"),
        "fats_g": macros.get("fats_g"),
        "meals": {
            "breakfast": get_meal("breakfast"),
            "lunch": get_meal("lunch"),
            "dinner": get_meal("dinner"),
            "snacks": get_meal("snacks")
        },
        "note": f"Focus on hitting ~{macros.get('protein_g')}g protein today."
    }
