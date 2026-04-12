"""webhook.py — External trigger API for InkyPi.

Exposes simple REST endpoints that let external systems (Home Assistant,
scripts, cron jobs, IFTTT, etc.) control the display without touching the
web UI.

Authentication
--------------
Set the environment variable ``WEBHOOK_API_KEY`` to a secret string.
All requests must then include the header ``X-API-Key: <your-key>``.
If the variable is not set the endpoints are unprotected (fine for a
private LAN).

Endpoints
---------
POST /api/webhook/update
    Push a plugin to the display immediately with custom settings.
    Body (JSON): { "plugin_id": "clock", "settings": { ... } }

POST /api/webhook/next
    Advance the active playlist to the next plugin.

GET  /api/webhook/status
    Return the same payload as /api/status (convenience alias).
"""

import os
import logging
from functools import wraps

from flask import Blueprint, request, jsonify, current_app

from refresh_task import ManualRefresh, PlaylistRefresh

logger = logging.getLogger(__name__)
webhook_bp = Blueprint("webhook", __name__)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _require_api_key(f):
    """Decorator that enforces WEBHOOK_API_KEY when the env var is set."""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = os.environ.get("WEBHOOK_API_KEY", "").strip()
        if expected:
            provided = request.headers.get("X-API-Key", "").strip()
            if provided != expected:
                logger.warning("Webhook: rejected request with invalid API key.")
                return jsonify({"error": "Unauthorized — invalid or missing X-API-Key header"}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@webhook_bp.route("/api/webhook/update", methods=["POST"])
@_require_api_key
def webhook_update():
    """Immediately push a plugin to the display with the provided settings.

    Request JSON:
        plugin_id (str, required): The plugin id to display.
        settings  (dict, optional): Plugin settings dict. Defaults to {}.

    Returns 200 on success, 4xx/5xx on error.
    """
    device_config = current_app.config["DEVICE_CONFIG"]
    refresh_task = current_app.config["REFRESH_TASK"]

    data = request.get_json(silent=True) or {}
    plugin_id = data.get("plugin_id", "").strip()
    plugin_settings = data.get("settings", {})

    if not plugin_id:
        return jsonify({"error": "plugin_id is required"}), 400

    plugin_config = device_config.get_plugin(plugin_id)
    if not plugin_config:
        return jsonify({"error": f"Unknown plugin '{plugin_id}'"}), 404

    try:
        refresh_task.manual_update(ManualRefresh(plugin_id, plugin_settings))
    except Exception as e:
        logger.exception("Webhook update failed.")
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": True, "message": f"Display updated with plugin '{plugin_id}'."})


@webhook_bp.route("/api/webhook/next", methods=["POST"])
@_require_api_key
def webhook_next():
    """Advance the active playlist to the next plugin and update the display.

    No request body needed.
    """
    device_config = current_app.config["DEVICE_CONFIG"]
    refresh_task = current_app.config["REFRESH_TASK"]

    try:
        import pytz
        from datetime import datetime
        tz_str = device_config.get_config("timezone", default="UTC")
        now = datetime.now(pytz.timezone(tz_str))

        playlist_manager = device_config.get_playlist_manager()
        playlist = playlist_manager.determine_active_playlist(now)
        if not playlist:
            return jsonify({"error": "No active playlist at this time"}), 400
        if not playlist.plugins:
            return jsonify({"error": "Active playlist has no plugins"}), 400

        plugin_instance = playlist.get_next_plugin()
        refresh_task.manual_update(PlaylistRefresh(playlist, plugin_instance, force=True))
    except Exception as e:
        logger.exception("Webhook next failed.")
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": True, "message": "Advanced to next plugin in playlist."})


@webhook_bp.route("/api/webhook/status", methods=["GET"])
@_require_api_key
def webhook_status():
    """Convenience alias for /api/status — useful for external monitoring."""
    from blueprints.main import get_status
    return get_status()
