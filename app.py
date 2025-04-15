from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import random
import csv
from datetime import datetime
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

DATA_DIR = "data"
RESULT_DIR = "results"
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_quiz():
    topic = request.form.get("topic")
    level = request.form.get("level")
    sub_category = request.form.get("sub_category")

    if topic in ["grammar", "vocab", "idioms"]:
        filename = f"{topic}{sub_category}_{level}.json"
    else:
        filename = f"{topic}_{level}.json"

    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return f"<h1>파일 '{filename}'이 존재하지 않습니다.</h1>", 404

    with open(filepath, "r", encoding="utf-8") as f:
        questions = json.load(f)
    random.shuffle(questions)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+", encoding="utf-8")
    json.dump(questions, tmp, ensure_ascii=False, indent=2)
    tmp.flush()
    tmp_path = tmp.name
    tmp.close()

    session.clear()
    session["filename"] = tmp_path
    session["index"] = 0
    session["score"] = 0
    session["answers"] = []
    session["topic"] = topic
    session["level"] = level
    session["sub_category"] = sub_category

    return redirect(url_for("quiz"))

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "filename" not in session:
        return redirect(url_for("index"))

    filename = session["filename"]
    try:
        with open(filename, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except Exception as e:
        return f"<h1>퀴즈 데이터를 불러오는 중 에러 발생: {str(e)}</h1>", 500

    index = session.get("index", 0)
    total = len(questions)

    if index >= total:
        return redirect(url_for("result"))

    current_question = questions[index]

    if request.method == "POST":
        selected = request.form.get("option")
        correct_answer = current_question["answer"]

        answer_record = {
            "question": current_question["question"],
            "correct_answer": correct_answer,
            "user_answer": selected
        }
        answers = session.get("answers", [])
        answers.append(answer_record)
        session["answers"] = answers

        if selected == correct_answer:
            session["score"] = session.get("score", 0) + 1

        session["index"] = index + 1

        if session["index"] >= total:
            return redirect(url_for("result"))
        else:
            return redirect(url_for("quiz"))

    return render_template("quiz.html", q=current_question, index=index + 1, total=total)

@app.route("/result")
def result():
    answers = session.get("answers", [])
    correct = [a for a in answers if a["user_answer"] == a["correct_answer"]]
    wrong = [a for a in answers if a["user_answer"] != a["correct_answer"]]
    score = session.get("score", 0)
    total = len(answers)
    return render_template("result.html", score=score, total=total, correct=correct, wrong=wrong)

@app.route("/save_score", methods=["POST"])
def save_score():
    username = request.form.get("username", "익명")
    score = session.get("score", 0)
    topic = session.get("topic", "")
    level = session.get("level", "")
    sub_category = session.get("sub_category", "")
    total = len(session.get("answers", []))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ranking_path = os.path.join(RESULT_DIR, "ranking.csv")

    file_exists = os.path.exists(ranking_path)
    with open(ranking_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "username", "topic", "sub_category", "level", "score", "total"])
        writer.writerow([now, username, topic, sub_category, level, score, total])
    
    return redirect(url_for("ranking"))

@app.route("/ranking")
def ranking():
    ranking_path = os.path.join(RESULT_DIR, "ranking.csv")
    entries = []

    if os.path.exists(ranking_path):
        with open(ranking_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["score"] = int(row["score"])
                row["total"] = int(row["total"])
                entries.append(row)
    entries.sort(key=lambda x: x["score"], reverse=True)
    return render_template("ranking.html", entries=entries)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
