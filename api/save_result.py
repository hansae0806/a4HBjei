# api/save_result.py
import json
import os
from datetime import datetime

RESULT_DIR = "results"
os.makedirs(RESULT_DIR, exist_ok=True)

def handler(request):
    try:
        body = request.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        username = body.get("username", "anonymous")
        score = body.get("score")
        topic = body.get("topic")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{timestamp}.json"

        filepath = os.path.join(RESULT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, indent=2)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "저장 완료", "file": filename})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"에러 발생: {str(e)}"
        }
