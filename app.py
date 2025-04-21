import os
import secrets
import requests
from flask import Flask, render_template, redirect, request, jsonify, session, url_for
from flask_caching import Cache
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from database import engine, SessionLocal, Base
from models import User, Bookmark, MealPlan
from helpers import is_new_day, generate_hash, check_hash
from dotenv import load_dotenv

load_dotenv()

# flask app setup
app = Flask(__name__)

# cache setuup
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600
cache = Cache(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv("SECRET_KEY")

Session(app)
csrf = CSRFProtect(app)

Base.metadata.create_all(engine)

api_key = os.getenv('API_KEY')

print(f"API Key: {api_key}")

@app.route("/")
def index():
    db = SessionLocal()
    user_id = session.get("user_id")

    randomUrl = "https://api.spoonacular.com/recipes/random"
    url = "https://api.spoonacular.com/recipes/complexSearch"

    vegan_params = {
        'apiKey': api_key,
        'number': 12,
        'diet': 'vegan',
        'sort': 'random'
    }
    chicken_params ={
        'apiKey': api_key,
        'number': 12,
        'query': 'chicken',
        'includeIngredients': 'chicken',
        'sort': 'random'
    }
    try:
        recipes_data = cache.get("popular_recipes")
        if not recipes_data or is_new_day():
            # fetch popular recipe
            response = requests.get(randomUrl, params={'apiKey': api_key, 'number': 12})
            response.raise_for_status()
            recipes_data = response.json().get('recipes', [])
            cache.set("popular_recipes", recipes_data)

        vegan_data = cache.get("vegan_recipes")
        if not vegan_data or is_new_day():
            # fetch vegan recipe
            vegan_response = requests.get(url, params=vegan_params)
            vegan_response.raise_for_status()
            vegan_data = vegan_response.json().get('results', [])
            cache.set("vegan_recipes", vegan_data)

        chicken_data = cache.get("chicken_recipes")
        if not chicken_data or is_new_day():
            # fetch quick recipes
            chicken_response = requests.get(url, params=chicken_params)
            chicken_response.raise_for_status()
            chicken_data = chicken_response.json().get('results', [])
            cache.set("chicken_recipes", chicken_data)
    except Exception as e:
        recipes_data = []
        vegan_data = []
        chicken_data = []
        print(f"Error fetching recipes: {e}")
    finally:    
        bookmarked_recipes = set()
        if user_id:
            bookmarked_recipes = {b.recipe_id for b in db.query(Bookmark).filter_by(user_id=user_id).all()}
        db.close()

    return render_template("index.html",
                            recipes=recipes_data,
                            vegans=vegan_data, 
                            chickens=chicken_data,
                            bookmarked_recipes=bookmarked_recipes)

@app.route("/search-results")
def search():
    db = SessionLocal()
    user_id = session.get("user_id")
    query = request.args.get("query", "").strip()
    
    if not query:
        return redirect(url_for("index"))

    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": api_key,
        "query": query,
        "number": 12
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Make sure "results" exists, otherwise set an empty list
        recipes = data.get("results", [])
        
    except Exception as e:
        print(f"Search error: {e}")
        recipes = []  # Set empty list if an error occurs

    # Fetch user's bookmarked recipes
    bookmarked_recipes = set()
    if user_id:
        bookmarked_recipes = {b.recipe_id for b in db.query(Bookmark).filter_by(user_id=user_id).all()}
    db.close()

    return render_template("search-results.html", query=query, recipes=recipes, bookmarked_recipes=bookmarked_recipes)

@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"suggestions": []})  # Return empty list if no query

    url = "https://api.spoonacular.com/recipes/autocomplete"
    params = {
        "apiKey": api_key,
        "query": query,
        "number": 5
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        suggestions = [item["title"] for item in data]
    except Exception as e:
        print(f"Autocomplete error: {e}")
        suggestions = []

    return jsonify({"suggestions": suggestions})

@app.route("/recipe/<int:recipe_id>")
def recipe_info(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        'apiKey': api_key
    }
    try:
        recipe_details = cache.get(f"recipe_info_{recipe_id}")
        if not recipe_details:
            response = requests.get(url, params=params)
            response.raise_for_status()
            recipe_details = response.json()

            instructions_list = []
            if recipe_details.get("analyzedInstructions"):
                for step in recipe_details["analyzedInstructions"][0].get("steps", []):
                    instructions_list.append(step["step"])

            recipe_details["instructions_list"] = instructions_list
            cache.set(f"recipe_info_{recipe_id}", recipe_details)
    except Exception as e:
        recipe_details = {}
        print(f"Error fetching recipe details: {e}")

    return render_template("recipe-info.html", recipe=recipe_details)

@app.route("/generate-meal-plan", methods=["GET"])
def show_generate_meal_plan():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("generate-meal-plan.html")

@app.route("/generate-meal-plan", methods=["POST"])
def generate_meal_plan():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401
        
    db = SessionLocal()
    user_id = session["user_id"]

    diet = request.form.get("diet", "")
    calories = request.form.get("calories", "")
    exclude = request.form.get("exclude", "")

    url = "https://api.spoonacular.com/mealplanner/generate"
    params = {
        "apiKey": api_key,
        "timeFrame": "week", # weekly meal plan
    }

    if diet: 
        params["diet"] = diet
    if calories:
        params["targetCalories"] = calories
    if exclude:
        params["exclude"]  = exclude
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        meal_plan_data = response.json()

        new_plan = MealPlan(user_id=user_id, plan_data=meal_plan_data)
        db.add(new_plan)
        db.commit()

        db.close()
        return redirect("/meal-plan")
    except Exception as e:
        db.close()
        print(f"Error generating meal plan: {e}")
        return jsonify({"success": False, "message": "Failed to generate meal plan"}), 500

@app.route("/meal-plan")
def meal_plan():
    if "user_id" not in session:
        return redirect("/login")
    
    db = SessionLocal()
    user_id = session["user_id"]

    meal_plan = db.query(MealPlan).filter_by(user_id=user_id).order_by(MealPlan.generated_at.desc()).first()
    if meal_plan:
        for day_meals in meal_plan.plan_data["week"].values():
            for meal in day_meals["meals"]:
                meal["image"] = f"https://spoonacular.com/recipeImages/{meal['id']}-556x370.jpg"
    db.close()

    return render_template("meal-plan.html", meal_plan=meal_plan)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    db = SessionLocal()

    try:
        csrf_token_received = request.form.get("csrf_token")
        print("Received CSRF Token:", csrf_token_received)

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return jsonify({"success": False, "message": "All fields are required"}), 403
        if password != confirmation:
            return jsonify({"success": False, "message": "Passwords do not match"}), 403
        
        existing_user = db.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({"success": False, "message": "User already exists"}), 400
        
        hashed_password = generate_hash(password)
    
        # create new user
        new_user = User(username=username, password_hash=hashed_password)
        db.add(new_user)
        db.commit()

        return jsonify({"success": True, "message": "Registered Successfully"}), 200
    except Exception as e:
        print(f"Error: {e}") 
        return jsonify({"success": False, "message": "Unexpected error. Try again later"}), 403
    finally:
        db.close()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    db = SessionLocal()

    try:
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return jsonify({"success": False, "message": "All fields are required"}), 403
        
        user = db.query(User).filter_by(username=username).first()

        if not user or not check_hash(password, user.password_hash):
            return jsonify({"success": False, "message": "Invalid username or password"}), 403
        
        session["user_id"] = user.id

        return jsonify({"success": True, "message": "Login successful"}), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": "Unexpected error. Try again later"}), 500
    
    finally:
        db.close()

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    print("Session after logout: ", session)
    return redirect("/")

@app.route("/bookmark", methods=["POST"])
def bookmark_recipe():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401
    
    db = SessionLocal()
    user_id = session["user_id"]

    print("Bookmark request received!")

    recipe_id = request.form.get("recipe_id")
    title = request.form.get("title")
    image = request.form.get("image")

    print(f"Recipe ID: {recipe_id}, Title: {title}, Image: {image}")

    if not recipe_id or not title or not image:
        print("ERROR: Missing recipe data!")
        return jsonify({"success": False, "message": "Missing recipe data"}), 400

    existing_bookmark = db.query(Bookmark).filter_by(user_id=user_id, recipe_id=recipe_id).first()
    if existing_bookmark:
        db.delete(existing_bookmark)
        db.commit()
        db.close()
        print("Bookmark removed!")
        return jsonify({"success": True, "message": "Bookmark removed", "bookmarked": False})
    
    new_bookmark = Bookmark(user_id=user_id, recipe_id=recipe_id, title=title, image=image)
    db.add(new_bookmark)
    db.commit()
    db.close()

    print("Recipe bookmarked!")
    return jsonify({"success": True, "message": "Recipe Bookmarked!"})

@app.route("/bookmarks")
def get_bookmarks():
    if "user_id" not in session:
        return redirect("/login")
    
    db = SessionLocal()
    user_id = session["user_id"]
    print("User ID from session:", user_id)
    bookmarks = db.query(Bookmark).filter_by(user_id=user_id).all()
    db.close()

    return render_template("bookmarks.html", bookmarks=bookmarks)

@app.route("/bookmark/delete", methods=["POST"])
def delete_bookmark():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401
    
    db = SessionLocal()
    user_id = session["user_id"]
    recipe_id = request.form.get("recipe_id")

    print(f"Delete request received: RecipeID={recipe_id}")
    
    if not recipe_id:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    bookmark = db.query(Bookmark).filter_by(user_id=user_id, recipe_id=recipe_id).first()
    if not bookmark:
        return jsonify({"success": False, "message": "Bookmark not found"}), 404
    
    db.delete(bookmark)
    db.commit()
    db.close()

    return jsonify ({"success": True, "message": "Bookmark removed!"})

if __name__ == '__main__':
    app.run(debug=True)