import uuid
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json()

    # Validate input
    if not data or not data.get("text") or not data.get("creator_id"):
        return jsonify({"error": "text and creator_id are required"}), 400

    # Placeholder response — real logic comes in Milestone 3/4
    content_id = str(uuid.uuid4())
    return jsonify({
        "content_id": content_id,
        "attribution": "pending",
        "confidence": 0.0,
        "label": "Analysis not yet implemented"
    })


@app.route("/log", methods=["GET"])
def get_log():
    return jsonify({"entries": []})


@app.route("/appeal", methods=["POST"])
def appeal():
    return jsonify({"message": "Appeal endpoint not yet implemented"}), 501


if __name__ == "__main__":
    app.run(debug=True)