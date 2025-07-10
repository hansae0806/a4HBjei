import json
import os

def handler(request):
    try:
        body = request.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        topic = body.get("topic")
        level = body.get("level")
        sub_category = body.get("sub_category")

        if topic in ["grammar", "vocab", "idioms"]:
            filename = f"{topic}{sub_category}_{level}.json"
        else:
            filename = f"{topic}_{level}.json"

        filepath = os.path.join("data", filename)

        if not os.path.exists(filepath):
            return {
                "statusCode": 404,
                "body": f"파일 {filename}이 존재하지 않습니다."
            }

        with open(filepath, "r", encoding="utf-8") as f:
            questions = json.load(f)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(questions)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"오류 발생: {str(e)}"
        }
