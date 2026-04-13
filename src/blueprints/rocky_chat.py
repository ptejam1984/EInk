"""rocky_chat.py — Live chat API for the Rocky companion plugin.

POST /api/rocky/chat   — send a message, get Rocky's response
POST /api/rocky/mood   — generate a fresh Rocky message for a given mood
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from plugins.rocky.rocky import Rocky

logger = logging.getLogger(__name__)
rocky_bp = Blueprint("rocky", __name__)


@rocky_bp.route("/api/rocky/chat", methods=["POST"])
def rocky_chat():
    """Chat with Rocky.

    Request JSON:
        message  (str): What the human says to Rocky.
        history  (list, optional): Previous [{"role","content"},...] messages.

    Response JSON:
        { "response": "<Rocky's reply>", "mood": "chat" }
    """
    device_config = current_app.config["DEVICE_CONFIG"]
    api_key = device_config.load_env_key("OPEN_AI_SECRET")
    if not api_key:
        return jsonify({"error": "OPEN_AI_SECRET not configured. Add it via the API Keys page."}), 400

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    try:
        reply = Rocky.generate_rocky_message(
            api_key,
            mood="chat",
            user_message=user_message,
            history=history,
        )
        return jsonify({"response": reply, "mood": "chat"})
    except Exception as e:
        logger.exception("Rocky chat failed.")
        return jsonify({"error": str(e)}), 500


@rocky_bp.route("/api/rocky/mood", methods=["POST"])
def rocky_mood():
    """Generate a fresh Rocky message for a specific mood (no user input needed).

    Request JSON:
        mood (str): One of greeting / science / humor / emotional / evening.

    Response JSON:
        { "response": "<Rocky's message>", "mood": "<mood>" }
    """
    device_config = current_app.config["DEVICE_CONFIG"]
    api_key = device_config.load_env_key("OPEN_AI_SECRET")
    if not api_key:
        return jsonify({"error": "OPEN_AI_SECRET not configured."}), 400

    data = request.get_json(silent=True) or {}
    mood = data.get("mood", "greeting")

    try:
        reply = Rocky.generate_rocky_message(api_key, mood=mood)
        return jsonify({"response": reply, "mood": mood})
    except Exception as e:
        logger.exception("Rocky mood generation failed.")
        return jsonify({"error": str(e)}), 500
