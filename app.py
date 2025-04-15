from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import random
import csv
from datetime import datetime
import tempfile

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

    # tempfile로 문제 저장
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+", encoding="utf-8")
    json.dump(questions, tmp, ensure_ascii=False, indent=2)
    tmp.flush()
    tmp_path = tmp.name
    tmp.close()

    session["filename"] = tmp_path
    session["index"] = 0
    session["score"] = 0
    session["topic"] = topic
    session["level"] = level

    return redirect(url_for("quiz"))

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "filename" not in session or session["index"] >= len(session["questions"]):
        return redirect(url_for("index"))

    # 퀴즈 문제 불러오기
    filename = session["filename"]
    with open(filename, "r", encoding="utf-8") as f:
        questions = json.load(f)

    index = session["index"]
    current_question = questions[index]

    if request.method == "POST":
        selected = request.form.get("option")
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
            return redirect(url_for("result"))

    return render_template("quiz.html", q=current_question, index=index + 1, total=len(questions))

@app.route("/result")
def result():
    answers = session.get("answers", [])
    correct_answers = [a for a in answers if a["user_answer"] == a["correct_answer"]]
    wrong_answers = [a for a in answers if a["user_answer"] != a["correct_answer"]]
    return render_template("result.html", score=len(correct_answers), total=len(answers),
                           correct=correct_answers, wrong=wrong_answers)

@app.route("/save_score", methods=["POST"])
def save_score():
    username = request.form.get("username", "익명")
    score = session.get("score", 0)
    topic = session.get("topic", "")
    level = session.get("level", "")
    filename = session.get("filename")

    total = 0
    if filename and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            total = len(json.load(f))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ranking_path = os.path.join(RESULT_DIR, "ranking.csv")

    with open(ranking_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now, username, topic, level, score, total])

    return redirect(url_for("ranking"))

@app.route("/ranking")
def ranking():
    ranking_path = os.path.join(RESULT_DIR, "ranking.csv")
    entries = []

    if os.path.exists(ranking_path):
        with open(ranking_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                entries.append({
                    "time": row[0],
                    "username": row[1],
                    "topic": row[2],
                    "level": row[3],
                    "score": int(row[4]),
                    "total": int(row[5])
                })

    # 점수 기준 내림차순 정렬
    entries.sort(key=lambda x: x["score"], reverse=True)

    return render_template("ranking.html", entries=entries)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
