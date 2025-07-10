# api/load_result.py
import os
import json

RESULT_DIR = "results"

def handler(request):
    try:
        if not os.path.exists(RESULT_DIR):
            return {
                "statusCode": 200,
                "body": json.dumps([])
            }

        files = [f for f in os.listdir(RESULT_DIR) if f.endswith(".json")]
        result_list = []

        for fname in sorted(files, reverse=True):
            with open(os.path.join(RESULT_DIR, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                result_list.append(data)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result_list)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"에러 발생: {str(e)}"
        }
