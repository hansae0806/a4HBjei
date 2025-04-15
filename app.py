from flask import Flask, render_template, request, redirect, url_for, session
import json, random, os, csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

DATA_DIR = "data"
RESULT_DIR = "results"
os.makedirs(RESULT_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_quiz():
    topic = request.form["topic"]
    level = request.form["level"]
    filename = f"{topic}_{level}.json"
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        return f"<h3>{filename} 파일이 없습니다.</h3>"

    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)
    random.shuffle(questions)
    session["questions"] = questions
    session["index"] = 0
    session["score"] = 0
    session["answers"] = []

    return redirect(url_for("quiz"))

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "questions" not in session:
        return redirect(url_for("index"))

    questions = session["questions"]
    index = session["index"]
    score = session["score"]
    answers = session["answers"]

    if request.method == "POST":
        selected = request.form.get("option")
        correct = questions[index]["answer"]
        answers.append({
            "question": questions[index]["question"],
            "correct_answer": correct,
            "user_answer": selected
        })
        if selected == correct:
            score += 1

        index += 1
        session["index"] = index
        session["score"] = score
        session["answers"] = answers

        if index >= len(questions):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(os.path.join(RESULT_DIR, "quiz_log.csv"), "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([now, request.form.get("topic", ""), request.form.get("level", ""), score, len(questions)])
            return redirect(url_for("result"))

    if index < len(questions):
        q = questions[index]
        return render_template("quiz.html", q=q, index=index + 1, total=len(questions))

@app.route("/result")
def result():
    answers = session.get("answers", [])
    correct = [a for a in answers if a["user_answer"] == a["correct_answer"]]
    wrong = [a for a in answers if a["user_answer"] != a["correct_answer"]]
    return render_template("result.html", score=len(correct), total=len(answers), correct=correct, wrong=wrong)

if __name__ == "__main__":
    app.run(debug=True)