from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import random
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")  # 배포 시 환경 변수로 변경 가능

# 데이터 및 결과 경로 설정
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
    filename = f"{topic}_{level}.json"
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return f"<h1>파일 '{filename}'이 존재하지 않습니다.</h1>", 404

    with open(filepath, "r", encoding="utf-8") as f:
        questions = json.load(f)
    random.shuffle(questions)

    # 세션에 퀴즈 데이터 저장
    session["questions"] = questions
    session["index"] = 0
    session["score"] = 0
    session["answers"] = []
    session["topic"] = topic
    session["level"] = level

    return redirect(url_for("quiz"))

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "questions" not in session or session["index"] >= len(session["questions"]):
        return redirect(url_for("index"))

    questions = session["questions"]
    index = session["index"]

    if request.method == "POST":
        selected = request.form.get("option")
        current_question = questions[index]
        correct_answer = current_question["answer"]

        # 사용자의 답변 기록
        session["answers"].append({
            "question": current_question["question"],
            "correct_answer": correct_answer,
            "user_answer": selected
        })

        if selected == correct_answer:
            session["score"] += 1

        session["index"] += 1

        if session["index"] >= len(questions):
            # 결과 로그 CSV 파일에 기록
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            csv_path = os.path.join(RESULT_DIR, "quiz_log.csv")
            with open(csv_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([now, session.get("topic", ""), session.get("level", ""), session["score"], len(questions)])
            return redirect(url_for("result"))

    # 다음 문제 준비
    index = session["index"]
    current_question = questions[index]
    return render_template("quiz.html", q=current_question, index=index+1, total=len(questions))

@app.route("/result")
def result():
    answers = session.get("answers", [])
    correct_answers = [a for a in answers if a["user_answer"] == a["correct_answer"]]
    wrong_answers = [a for a in answers if a["user_answer"] != a["correct_answer"]]
    return render_template("result.html", score=len(correct_answers), total=len(answers),
                           correct=correct_answers, wrong=wrong_answers)

if __name__ == "__main__":
    # Railway에서 PORT 환경변수를 받아서 실행 (기본 5000번 포트)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
