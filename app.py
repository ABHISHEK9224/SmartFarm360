import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# --------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

# Secret key for Flask sessions
app.secret_key = os.getenv(
    "SECRET_KEY",
    "smartfarm360-development-secret-key"
)

# --------------------------------------------------
# MONGODB CONNECTION
# --------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI")

mongo_client = None
mongo_db = None
users_collection = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        # Test the connection
        mongo_client.admin.command("ping")

        mongo_db = mongo_client["SmartFarm360"]
        users_collection = mongo_db["users"]

        print("MongoDB connected successfully!")

    except Exception as e:
        print("MongoDB connection failed:", e)

else:
    print("MONGO_URI not found in .env file.")


# --------------------------------------------------
# CROP DATA
# --------------------------------------------------

crop_data = {
    "Maize": {
        "soil": ["Black Soil", "Red Soil", "Loamy"],
        "season": ["Kharif", "Rabi"],
        "water": ["Medium", "High"],
        "water_required": "Medium",
        "cost_per_acre": 10000,
        "yield_per_acre": 20,
        "price_per_unit": 2200,
        "seed_per_acre": 8,
        "fertilizer_per_acre": 200,
        "labour_per_acre": 5
    },

    "Cotton": {
        "soil": ["Black Soil", "Loamy"],
        "season": ["Kharif"],
        "water": ["Medium", "High"],
        "water_required": "Medium",
        "cost_per_acre": 12000,
        "yield_per_acre": 8,
        "price_per_unit": 7000,
        "seed_per_acre": 5,
        "fertilizer_per_acre": 250,
        "labour_per_acre": 5
    },

    "Chickpea": {
        "soil": ["Black Soil", "Red Soil", "Loamy"],
        "season": ["Rabi"],
        "water": ["Low", "Medium"],
        "water_required": "Low",
        "cost_per_acre": 9000,
        "yield_per_acre": 15,
        "price_per_unit": 5500,
        "seed_per_acre": 15,
        "fertilizer_per_acre": 150,
        "labour_per_acre": 4
    },

    "Wheat": {
        "soil": ["Loamy", "Black Soil"],
        "season": ["Rabi"],
        "water": ["Medium", "High"],
        "water_required": "Medium",
        "cost_per_acre": 11000,
        "yield_per_acre": 18,
        "price_per_unit": 2600,
        "seed_per_acre": 20,
        "fertilizer_per_acre": 180,
        "labour_per_acre": 5
    },

    "Rice": {
        "soil": ["Clayey", "Loamy"],
        "season": ["Kharif"],
        "water": ["High"],
        "water_required": "High",
        "cost_per_acre": 15000,
        "yield_per_acre": 25,
        "price_per_unit": 2500,
        "seed_per_acre": 8,
        "fertilizer_per_acre": 250,
        "labour_per_acre": 8
    },

    "Tomato": {
        "soil": ["Loamy", "Sandy"],
        "season": ["Kharif", "Rabi", "Summer"],
        "water": ["Medium", "High"],
        "water_required": "High",
        "cost_per_acre": 14000,
        "yield_per_acre": 30,
        "price_per_unit": 1800,
        "seed_per_acre": 0.2,
        "fertilizer_per_acre": 200,
        "labour_per_acre": 8
    }
}


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# ABOUT
# --------------------------------------------------

@app.route("/about")
def about():
    return render_template("about.html")


# --------------------------------------------------
# CONTACT
# --------------------------------------------------

@app.route("/contact")
def contact():
    return render_template("contact.html")


# --------------------------------------------------
# AGRICULTURAL OFFICERS
# --------------------------------------------------

@app.route("/officers")
def officers():
    return render_template("officers.html")


# --------------------------------------------------
# ADMIN
# --------------------------------------------------

@app.route("/admin")
def admin():
    return render_template("admin.html")


# --------------------------------------------------
# FARM INPUT
# --------------------------------------------------

@app.route("/farm-input")
def farm_input():
    return render_template("farm-input.html")


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Basic validation
        if not full_name or not email or not password:
            flash("Please fill in all required fields.")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        # Check MongoDB connection
        if users_collection is None:
            flash("Database connection is not available.")
            return redirect(url_for("register"))

        # Check whether email already exists
        existing_user = users_collection.find_one(
            {"email": email}
        )

        if existing_user:
            flash("An account with this email already exists.")
            return redirect(url_for("register"))

        # Securely hash password
        password_hash = generate_password_hash(password)

        # Create user document
        user_document = {
            "full_name": full_name,
            "email": email,
            "password_hash": password_hash
        }

        users_collection.insert_one(user_document)

        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:
            flash("Please enter your email and password.")
            return redirect(url_for("login"))

        if users_collection is None:
            flash("Database connection is not available.")
            return redirect(url_for("login"))

        # Find user
        user = users_collection.find_one(
            {"email": email}
        )

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session.clear()

            session["user_id"] = str(user["_id"])
            session["user_name"] = user["full_name"]
            session["user_email"] = user["email"]

            flash(
                f"Welcome, {user['full_name']}!"
            )

            return redirect(url_for("home"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("home"))


# --------------------------------------------------
# GENERATE FARM PLAN
# --------------------------------------------------

@app.route("/generate-plan", methods=["POST"])
def generate_plan():

    land_area = float(
        request.form.get("land_area", 0)
    )

    soil_type = request.form.get(
        "soil_type"
    )

    water_availability = request.form.get(
        "water_availability"
    )

    season = request.form.get(
        "season"
    )

    budget = float(
        request.form.get("budget", 0)
    )

    preferred_crop = request.form.get(
        "preferred_crop"
    )

    crop_scores = []

    for crop_name, data in crop_data.items():

        score = 0
        reasons = []

        # Soil
        if soil_type in data["soil"]:
            score += 30
            reasons.append("Suitable soil")

        # Season
        if season in data["season"]:
            score += 25
            reasons.append("Suitable season")

        # Water
        if water_availability in data["water"]:
            score += 20
            reasons.append(
                "Suitable water availability"
            )

        # Cost
        estimated_cost = (
            data["cost_per_acre"] * land_area
        )

        if estimated_cost > 0:
            budget_coverage = (
                budget / estimated_cost
            ) * 100
        else:
            budget_coverage = 0

        if budget_coverage > 100:
            budget_coverage = 100

        # Budget score
        if budget >= estimated_cost:

            score += 15

            reasons.append(
                "Budget covers estimated cost"
            )

        elif budget >= estimated_cost * 0.5:

            score += 8

            reasons.append(
                "Partially covered by available budget"
            )

        else:

            reasons.append(
                "Budget may be insufficient"
            )

        # Preferred crop
        if (
            preferred_crop
            and preferred_crop == crop_name
        ):

            score += 10

            reasons.append(
                "Your preferred crop"
            )

        if score > 100:
            score = 100

        crop_scores.append({
            "name": crop_name,
            "score": score,
            "reasons": reasons,
            "estimated_cost": estimated_cost,
            "budget_coverage": budget_coverage
        })

    # Sort recommendations
    crop_scores.sort(
        key=lambda x: (
            x["score"],
            x["budget_coverage"]
        ),
        reverse=True
    )

    recommended_crop = crop_scores[0]["name"]

    selected_crop = crop_data[
        recommended_crop
    ]

    # Financial calculations
    estimated_cost = (
        selected_crop["cost_per_acre"]
        * land_area
    )

    expected_yield = (
        selected_crop["yield_per_acre"]
        * land_area
    )

    estimated_revenue = (
        expected_yield
        * selected_crop["price_per_unit"]
    )

    estimated_profit = (
        estimated_revenue
        - estimated_cost
    )

    # Budget coverage
    if estimated_cost > 0:

        budget_coverage_percent = (
            budget / estimated_cost
        ) * 100

    else:

        budget_coverage_percent = 0

    if budget_coverage_percent > 100:
        budget_coverage_percent = 100

    budget_gap = max(
        0,
        estimated_cost - budget
    )

    if budget_gap > 0:

        budget_status = (
            "Your available budget is lower "
            "than the estimated cultivation cost."
        )

    else:

        budget_status = (
            "Your available budget covers "
            "the estimated cultivation cost."
        )

    # Risk
    risk_level = "Low"

    if budget_coverage_percent < 50:
        risk_level = "Medium"

    if (
        water_availability
        not in selected_crop["water"]
    ):
        risk_level = "High"

    # Resources
    seeds_required = (
        selected_crop["seed_per_acre"]
        * land_area
    )

    fertilizer_required = (
        selected_crop["fertilizer_per_acre"]
        * land_area
    )

    labour_required = (
        selected_crop["labour_per_acre"]
        * land_area
    )

    seed_unit = "kg"
    fertilizer_unit = "kg"
    yield_unit = "quintals"

    return render_template(
        "farm-result.html",

        recommended_crop=recommended_crop,

        crop_scores=crop_scores,

        land_area=land_area,

        soil_type=soil_type,

        water_availability=water_availability,

        season=season,

        budget=budget,

        water_required=selected_crop[
            "water_required"
        ],

        estimated_cost=estimated_cost,

        expected_yield=expected_yield,

        yield_unit=yield_unit,

        risk_level=risk_level,

        budget_coverage_percent=
            budget_coverage_percent,

        budget_gap=budget_gap,

        budget_status=budget_status,

        estimated_revenue=
            estimated_revenue,

        estimated_profit=
            estimated_profit,

        seeds_required=seeds_required,

        fertilizer_required=
            fertilizer_required,

        labour_required=
            labour_required,

        seed_unit=seed_unit,

        fertilizer_unit=fertilizer_unit
    )


# --------------------------------------------------
# CROP SCHEDULE
# --------------------------------------------------

@app.route("/crop-schedule/<crop_name>")
def crop_schedule(crop_name):

    schedules = {

        "Maize": [
            (
                "Week 1",
                "🌱 Land Preparation",
                "Prepare the field, remove weeds and loosen the soil."
            ),
            (
                "Week 2",
                "🌽 Seed Sowing",
                "Sow good-quality maize seeds at suitable spacing."
            ),
            (
                "Week 3–4",
                "💧 Irrigation",
                "Monitor soil moisture and provide water when required."
            ),
            (
                "Week 5–8",
                "🌿 Fertilizer & Weed Management",
                "Manage weeds and apply fertilizer according to crop requirements."
            ),
            (
                "Week 9–12",
                "🔍 Crop Monitoring",
                "Check crop growth and monitor for pests and diseases."
            ),
            (
                "Harvest Stage",
                "🌾 Harvesting",
                "Harvest the maize when it reaches the appropriate maturity."
            )
        ],

        "Cotton": [
            (
                "Week 1",
                "🌱 Land Preparation",
                "Prepare the soil and remove weeds before sowing."
            ),
            (
                "Week 2",
                "🌱 Seed Sowing",
                "Sow suitable cotton seeds with proper spacing."
            ),
            (
                "Week 3–5",
                "💧 Irrigation",
                "Monitor soil moisture and provide irrigation when needed."
            ),
            (
                "Week 6–10",
                "🌿 Weed Management",
                "Control weeds and maintain healthy crop growth."
            ),
            (
                "Week 11–16",
                "🔍 Pest & Crop Monitoring",
                "Regularly check plants for pests, diseases and growth problems."
            ),
            (
                "Harvest Stage",
                "🌾 Cotton Harvest",
                "Harvest mature cotton bolls at the appropriate stage."
            )
        ],

        "Chickpea": [
            (
                "Week 1",
                "🌱 Land Preparation",
                "Prepare the field and ensure suitable soil conditions."
            ),
            (
                "Week 2",
                "🌿 Seed Sowing",
                "Sow healthy chickpea seeds at recommended spacing."
            ),
            (
                "Week 3–5",
                "💧 Water Monitoring",
                "Monitor soil moisture and avoid unnecessary irrigation."
            ),
            (
                "Week 6–9",
                "🌿 Weed Management",
                "Remove weeds and monitor crop development."
            ),
            (
                "Week 10–12",
                "🔍 Crop Monitoring",
                "Check for pests, diseases and signs of crop stress."
            ),
            (
                "Harvest Stage",
                "🌾 Harvesting",
                "Harvest when the plants and pods reach maturity."
            )
        ],

        "Wheat": [
            (
                "Week 1",
                "🌱 Field Preparation",
                "Prepare and level the field before sowing."
            ),
            (
                "Week 2",
                "🌾 Seed Sowing",
                "Sow quality wheat seeds at recommended spacing."
            ),
            (
                "Week 3–5",
                "💧 Irrigation",
                "Monitor soil moisture and irrigate according to crop needs."
            ),
            (
                "Week 6–10",
                "🌿 Fertilizer & Weed Management",
                "Manage weeds and apply fertilizer appropriately."
            ),
            (
                "Week 11–14",
                "🔍 Crop Monitoring",
                "Monitor crop growth and check for pests and diseases."
            ),
            (
                "Harvest Stage",
                "🌾 Harvesting",
                "Harvest when the wheat crop reaches maturity."
            )
        ],

        "Rice": [
            (
                "Week 1",
                "🌱 Field Preparation",
                "Prepare the field and maintain suitable moisture conditions."
            ),
            (
                "Week 2–3",
                "🌾 Planting",
                "Plant healthy rice seedlings using suitable spacing."
            ),
            (
                "Week 4–8",
                "💧 Water Management",
                "Maintain appropriate water levels according to crop conditions."
            ),
            (
                "Week 9–12",
                "🌿 Fertilizer & Weed Management",
                "Manage weeds and apply fertilizer as required."
            ),
            (
                "Week 13–16",
                "🔍 Crop Monitoring",
                "Monitor crop health and check for pests and diseases."
            ),
            (
                "Harvest Stage",
                "🌾 Harvesting",
                "Harvest when the rice grains reach suitable maturity."
            )
        ],

        "Tomato": [
            (
                "Week 1",
                "🌱 Soil Preparation",
                "Prepare fertile soil and create suitable planting beds."
            ),
            (
                "Week 2",
                "🍅 Planting",
                "Plant healthy tomato seedlings with proper spacing."
            ),
            (
                "Week 3–5",
                "💧 Irrigation",
                "Maintain regular moisture without excessive watering."
            ),
            (
                "Week 6–9",
                "🌿 Fertilizer & Support",
                "Provide nutrients and support plants as they grow."
            ),
            (
                "Week 10–14",
                "🔍 Pest & Disease Monitoring",
                "Regularly check plants for pests and diseases."
            ),
            (
                "Harvest Stage",
                "🍅 Harvesting",
                "Harvest tomatoes when they reach the desired maturity."
            )
        ]
    }

    if crop_name not in schedules:
        return "Crop schedule not available."

    return render_template(
        "crop-schedule.html",
        crop_name=crop_name,
        schedule=schedules[crop_name]
    )


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)