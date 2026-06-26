import uuid
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from signals import get_llm_score, get_stylo_score, combine_scores, get_label, get_attribution

load_dotenv()

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

LOG_FILE = "audit_log.json"


def write_log(entry: dict):
    try:
        with open(LOG_FILE, "r") as f:
            log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log = []
    log.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def read_log() -> list:
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json()

    if not data or not data.get("text") or not data.get("creator_id"):
        return jsonify({"error": "text and creator_id are required"}), 400

    text = data["text"]
    creator_id = data["creator_id"]
    content_id = str(uuid.uuid4())

    llm_score = get_llm_score(text)
    stylo_score = get_stylo_score(text)
    confidence = combine_scores(llm_score, stylo_score)
    attribution = get_attribution(confidence)
    label = get_label(confidence)

    entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "stylo_score": stylo_score,
        "status": "classified"
    }
    write_log(entry)

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label
    })


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json()

    if not data or not data.get("content_id") or not data.get("creator_reasoning"):
        return jsonify({"error": "content_id and creator_reasoning are required"}), 400

    content_id = data["content_id"]
    reasoning = data["creator_reasoning"]

    log = read_log()
    for entry in log:
        if entry["content_id"] == content_id:
            entry["status"] = "under_review"
            entry["appeal_reasoning"] = reasoning
            entry["appeal_timestamp"] = datetime.now(timezone.utc).isoformat()
            with open(LOG_FILE, "w") as f:
                json.dump(log, f, indent=2)
            return jsonify({
                "content_id": content_id,
                "status": "under_review",
                "message": "Your appeal has been received and will be reviewed."
            })

    return jsonify({"error": "content_id not found"}), 404


@app.route("/log", methods=["GET"])
def get_log():
    return jsonify({"entries": read_log()})


if __name__ == "__main__":
    app.run(debug=True)