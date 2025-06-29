import gradio as gr
from transformers import GPT2Tokenizer
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import textwrap

# Load GPT2 tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Estimate calorie needs using Mifflin-St Jeor Equation
def estimate_calories(weight, height, age, activity_level, goal, gender):
    if gender == "Male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    if activity_level == "Low":
        calories = bmr * 1.2
    elif activity_level == "Moderate":
        calories = bmr * 1.55
    elif activity_level == "High":
        calories = bmr * 1.75
    else:
        calories = bmr * 1.4  # reasonable default

    # Ensure goal is handled properly
    if goal == "Weight Loss":
        calories -= 400
    elif goal == "Muscle Gain":
        calories += 300
    elif goal == "Maintenance":
        calories = calories  # no change
    else:
        calories = calories  # no change for General Health

    return int(calories)

# Recommend meals based on multiple factors
def get_meal_plan(goal, diet_type, calories, bmi_cat, age, gender):
    meals = {"Breakfast": "", "Lunch": "", "Snack": "", "Dinner": ""}

    # Adjust portion sizes based on calorie range
    if calories < 1500:
        portion = "Small portions of "
    elif calories < 2200:
        portion = "Moderate portions of "
    else:
        portion = "Large portions of "

    # Base meal suggestions
    if diet_type == "Vegan":
        base_meals = {
            "Breakfast": f"{portion} of oats with almond milk, chia seeds, and berries",
            "Lunch": f"{portion} quinoa salad with chickpeas and avocado",
            "Snack": f"{portion} fruit smoothie with flaxseed",
            "Dinner": f"{portion} stir-fried tofu with vegetables and brown rice"
        }
    elif diet_type == "Vegetarian":
        base_meals = {
            "Breakfast": f"{portion} vegetable upma or poha with a glass of milk",
            "Lunch": f"{portion} dal, brown rice, mixed vegetable curry",
            "Snack": f"{portion} buttermilk and a banana",
            "Dinner": f"{portion} paneer bhurji with whole wheat roti"
        }
    elif diet_type == "Keto":
        base_meals = {
            "Breakfast": f"{portion} scrambled eggs with spinach and avocado",
            "Lunch": f"{portion} grilled chicken/fish with leafy greens",
            "Snack": f"{portion} boiled eggs or nuts",
            "Dinner": f"{portion} cauliflower rice with sautéed mushrooms and cheese"
        }
    elif diet_type == "Non-Vegetarian":
        base_meals = {
            "Breakfast": f"{portion} boiled eggs with whole wheat toast",
            "Lunch": f"{portion} grilled chicken with quinoa and veggies",
            "Snack": f"{portion} Greek yogurt with honey",
            "Dinner": f"{portion} fish curry with brown rice"
        }
    else:
        base_meals = {
            "Breakfast": f"{portion} oats, fruits, and milk",
            "Lunch": f"{portion} rice/roti, dal, vegetables",
            "Snack": f"{portion} dry fruits or sprouts",
            "Dinner": f"{portion} soup, salad, and light curry"
        }

    # Customize based on goal and BMI category
    for meal, item in base_meals.items():
        if goal == "Weight Loss" and bmi_cat in ["Overweight", "Obese"]:
            meals[meal] = f"{item} (reduced carbs, more fiber)"
        elif goal == "Muscle Gain" and bmi_cat in ["Normal", "Underweight"]:
            meals[meal] = f"{item} (high protein, healthy fats)"
        else:
            meals[meal] = f"{item} (balanced)"

    return meals

# Main function
def smart_diet_recommender(user_input, height, weight, gender):
    tokens = tokenizer.encode(user_input.lower())
    decoded_input = tokenizer.decode(tokens)

    if any(word in decoded_input for word in ["lose weight", "fat loss", "cut", "reduce weight"]):
      goal = "Weight Loss"
    elif any(word in decoded_input for word in ["gain muscle", "bulk", "muscle", "strong"]):
      goal = "Muscle Gain"
    elif any(word in decoded_input for word in ["maintain", "stay fit", "no change"]):
      goal = "Maintenance"
    else:
      goal = "General Health"


    if any(word in decoded_input for word in ["sedentary", "inactive", "lazy"]):
        activity = "Low"
    elif any(word in decoded_input for word in ["moderate", "walk", "jog"]):
        activity = "Moderate"
    elif any(word in decoded_input for word in ["active", "gym", "run", "exercise"]):
        activity = "High"
    else:
        activity = "Moderate"

    age = 0  # Default if not found
    for word in decoded_input.split():
        if word.isdigit() and 15 <= int(word) <= 100:
            age = int(word)
            break

    if "vegan" in decoded_input:
        diet_type = "Vegan"
    elif "vegetarian" in decoded_input:
        diet_type = "Vegetarian"
    elif "keto" in decoded_input:
        diet_type = "Keto"
    elif "pescatarian" in decoded_input:
        diet_type = "Pescatarian"
    elif any(word in decoded_input for word in ["meat", "non veg", "chicken", "fish", "mutton"]):
        diet_type = "Non-Vegetarian"
    else:
        diet_type = "General"

    if height and weight and height > 0 and weight > 0:
        height_m = height / 100
        bmi = round(weight / (height_m ** 2), 2)
        if bmi < 18.5:
            bmi_cat = "Underweight"
        elif bmi < 24.9:
            bmi_cat = "Normal"
        elif bmi < 29.9:
            bmi_cat = "Overweight"
        else:
            bmi_cat = "Obese"
    else:
        bmi = None
        bmi_cat = "Unknown"

    calorie_need = estimate_calories(weight, height, age, activity, goal, gender)
    meals = get_meal_plan(goal, diet_type, calorie_need, bmi_cat, age, gender)

    result = f"### 🥗 Your AI Diet Plan\n"
    result += f"**Goal**: {goal}\n"
    result += f"\n**Activity Level**: {activity}\n"
    result += f"\n**Diet Type**: {diet_type}\n"
    result += f"\n**Age**: {age}\n"
    result += f"\n**Gender**: {gender}\n"
    if bmi:
        result += f"\n**BMI**: {bmi} ({bmi_cat})\n"
    else:
        result += f"\n**BMI**: Not available"
    result += f"\n**Estimated Daily Calories**: {calorie_need} kcal\n\n"
    result += "\n### 🍱 Meal Schedule\n"
    for meal, items in meals.items():
        result += f"\n**{meal}**: {items}\n"
    return result

# PDF generation
def save_plan_to_pdf(user_input, height, weight, gender):
    plan = smart_diet_recommender(user_input, height, weight, gender)
    filepath = "/tmp/Diet_Plan.pdf"
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height_px = A4
    c.setFont("Helvetica", 12)
    y = height_px - 40

    for line in plan.split("\n"):
        wrapped = textwrap.wrap(line, width=90)
        for subline in wrapped:
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height_px - 40
            c.drawString(40, y, subline)
            y -= 18

    c.save()
    return filepath

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 🧠 DietGPT : Your AI-based Diet Recommender!")

    with gr.Row():
        user_input = gr.Textbox(
            label="Describe your age, goal, diet (e.g., vegetarian), and activity",
            placeholder="e.g., I'm a 25 year old vegetarian who wants to lose weight and jogs daily.",
            lines=4,
        )
        height = gr.Number(label="Height (cm)", value=None)
        weight = gr.Number(label="Weight (kg)", value=None)
        gender = gr.Radio(choices=["Male", "Female"], value=None, label="Gender")

    output = gr.Markdown(label="Generated Diet Plan")
    file_output = gr.File(label="Download Diet PDF")
    pdf_btn = gr.Button("📄 Generate PDF")

    def update_output(text, h, w, g):
        return smart_diet_recommender(text, h, w, g)

    user_input.change(update_output, [user_input, height, weight, gender], output)
    height.change(update_output, [user_input, height, weight, gender], output)
    weight.change(update_output, [user_input, height, weight, gender], output)
    gender.change(update_output, [user_input, height, weight, gender], output)

    pdf_btn.click(save_plan_to_pdf, [user_input, height, weight, gender], file_output)

demo.launch(share=True)