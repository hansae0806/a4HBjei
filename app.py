from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import random
import csv
from datetime import datetime
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

# 데이터 경로 (문제 JSON 파일은 data 폴더에 있어야 함)
DATA_DIR = "data"

# 결과 및 랭킹 저장 경로 (Railway에서는 휘발성이므로, 장기 저장을 원하면 DB 사용 고려)
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
    # data/ 폴더에 topic_level.json 파일이 있어야 함
    filename = f"{topic}_{level}.json"
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return f"<h1>파일 '{filename}'이 존재하지 않습니다.</h1>", 404

    with open(filepath, "r", encoding="utf-8") as f:
        questions = json.load(f)
    random.shuffle(questions)

    # tempfile을 이용해 셔플된 문제를 임시 파일로 저장 (프로덕션 시 자동 삭제되지 않으므로 세션 만료 후 정리 필요)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+", encoding="utf-8")
    json.dump(questions, tmp, ensure_ascii=False, indent=2)
    tmp.flush()
    tmp_path = tmp.name
    tmp.close()

    # 세션에는 문제 파일 경로와 진행 정보를 최소한으로 저장
    session.clear()
    session["filename"] = tmp_path
    session["index"] = 0
    session["score"] = 0
    # 정답 기록 (문제가 많지 않다면 세션에 기록해도 쿠키 용량 문제 없음)
    session["answers"] = []
    session["topic"] = topic
    session["level"] = level

    return redirect(url_for("quiz"))

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    # 세션에 필요한 정보가 없으면 인덱스로 복귀
    if "filename" not in session:
        return redirect(url_for("index"))

    filename = session["filename"]

    # 임시 파일에서 문제 로드
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

        # 정답/오답 기록: 기존 템플릿이 각 문제의 질문, 정답, 사용자의 선택을 출력하도록 함
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
    # 분류: 정답과 오답을 구분 (기존 템플릿에 맞게)
    correct = [a for a in answers if a["user_answer"] == a["correct_answer"]]
    wrong = [a for a in answers if a["user_answer"] != a["correct_answer"]]
    score = session.get("score", 0)
    total = len(answers)
    return render_template("result.html", score=score, total=total, correct=correct, wrong=wrong)

# 점수 저장 및 랭킹 기능: result.html에서 사용자 이름과 함께 점수를 저장할 수 있음
@app.route("/save_score", methods=["POST"])
def save_score():
    username = request.form.get("username", "익명")
    score = session.get("score", 0)
    topic = session.get("topic", "")
    level = session.get("level", "")
    
    # 총 문제 수는 세션의 answers 개수로 계산
    total = len(session.get("answers", []))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ranking_path = os.path.join(RESULT_DIR, "ranking.csv")

    # 랭킹 파일이 없으면 헤더 먼저 작성
    file_exists = os.path.exists(ranking_path)
    with open(ranking_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "username", "topic", "level", "score", "total"])
        writer.writerow([now, username, topic, level, score, total])
    
    return redirect(url_for("ranking"))

@app.route("/ranking")
def ranking():
    ranking_path = os.path.join(RESULT_DIR, "ranking.csv")
    entries = []

    if os.path.exists(ranking_path):
        with open(ranking_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # score와 total을 int로 변환
                row["score"] = int(row["score"])
                row["total"] = int(row["total"])
                entries.append(row)
    # 점수가 높은 순으로 정렬
    entries.sort(key=lambda x: x["score"], reverse=True)
    return render_template("ranking.html", entries=entries)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
