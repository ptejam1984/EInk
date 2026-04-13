"""rocky_chat.py — Live chat API for the Rocky companion plugin.

POST /api/rocky/chat   — send a message (or empty string for auto-greeting)
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from plugins.rocky.rocky import Rocky

logger = logging.getLogger(__name__)
rocky_bp = Blueprint("rocky", __name__)


@rocky_bp.route("/api/rocky/chat", methods=["POST"])
def rocky_chat():
    """Chat with Rocky — or get an automatic greeting when message is empty.

    Request JSON:
        message  (str): What the human says. Empty string = Rocky speaks first.
        history  (list, optional): Previous [{"role","content"},...] messages.

    Response JSON:
        { "response": "<Rocky's reply>" }
    """
    device_config = current_app.config["DEVICE_CONFIG"]
    api_key = device_config.load_env_key("OPEN_AI_SECRET")
    if not api_key:
        return jsonify({"error": "OPEN_AI_SECRET not set. Add it via the API Keys page."}), 400

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    try:
        # Empty message → Rocky auto-generates (same as display refresh)
        reply = Rocky.generate_rocky_message(api_key, user_message=user_message, history=history)
        return jsonify({"response": reply})
    except Exception as e:
        logger.exception("Rocky chat failed.")
        return jsonify({"error": str(e)}), 500
