import sys
import os

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set serverless environment flag
os.environ["NETLIFY"] = "true"
os.environ["SERVERLESS"] = "true"

try:
    from mangum import Mangum
    from server import app
    handler = Mangum(app)
except Exception as e:
    import json
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Failed to initialize serverless function",
                "detail": str(e)
            })
        }
