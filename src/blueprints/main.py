from flask import Blueprint, request, jsonify, current_app, render_template, send_file
import os
import psutil
from datetime import datetime

main_bp = Blueprint("main", __name__)

@main_bp.route('/')
def main_page():
    device_config = current_app.config['DEVICE_CONFIG']
    return render_template('inky.html', config=device_config.get_config(), plugins=device_config.get_plugins())

@main_bp.route('/api/current_image')
def get_current_image():
    """Serve current_image.png with conditional request support (If-Modified-Since)."""
    image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'current_image.png')
    
    if not os.path.exists(image_path):
        return jsonify({"error": "Image not found"}), 404
    
    # Get the file's last modified time (truncate to seconds to match HTTP header precision)
    file_mtime = int(os.path.getmtime(image_path))
    last_modified = datetime.fromtimestamp(file_mtime)
    
    # Check If-Modified-Since header
    if_modified_since = request.headers.get('If-Modified-Since')
    if if_modified_since:
        try:
            # Parse the If-Modified-Since header
            client_mtime = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S %Z')
            client_mtime_seconds = int(client_mtime.timestamp())
            
            # Compare (both now in seconds, no sub-second precision)
            if file_mtime <= client_mtime_seconds:
                return '', 304
        except (ValueError, AttributeError):
            pass
    
    # Send the file with Last-Modified header
    response = send_file(image_path, mimetype='image/png')
    response.headers['Last-Modified'] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['Cache-Control'] = 'no-cache'
    return response


@main_bp.route('/api/status')
def get_status():
    """Return live status: active playlist, last refresh, and system resource usage."""
    device_config = current_app.config['DEVICE_CONFIG']
    refresh_task = current_app.config['REFRESH_TASK']
    playlist_manager = device_config.get_playlist_manager()
    refresh_info = device_config.get_refresh_info()

    # Active playlist
    try:
        import pytz
        tz_str = device_config.get_config("timezone", default="UTC")
        now = datetime.now(pytz.timezone(tz_str))
        active_playlist = playlist_manager.determine_active_playlist(now)
        active_playlist_name = active_playlist.name if active_playlist else None
    except Exception:
        active_playlist_name = None
        now = datetime.utcnow()

    # System stats
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        system_stats = {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_mb": round(mem.used / 1024 / 1024, 1),
            "memory_total_mb": round(mem.total / 1024 / 1024, 1),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
        }
    except Exception:
        system_stats = {}

    return jsonify({
        "active_playlist": active_playlist_name,
        "refresh_task_running": refresh_task.running,
        "last_refresh": refresh_info.to_dict() if refresh_info else None,
        "current_time": now.isoformat(),
        "system": system_stats,
    })


@main_bp.route('/api/history')
def get_history():
    """Return the rolling display history log."""
    refresh_task = current_app.config['REFRESH_TASK']
    entries = refresh_task.history_manager.get_entries()
    return jsonify({"history": entries})


@main_bp.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Delete all display history entries and their thumbnails."""
    refresh_task = current_app.config['REFRESH_TASK']
    refresh_task.history_manager.clear()
    return jsonify({"success": True, "message": "Display history cleared."})


@main_bp.route('/api/history/image/<path:filename>')
def history_image(filename):
    """Serve a history thumbnail image."""
    refresh_task = current_app.config['REFRESH_TASK']
    image_dir = refresh_task.history_manager.image_dir
    safe_path = os.path.abspath(os.path.join(image_dir, filename))
    if not safe_path.startswith(os.path.abspath(image_dir)):
        return "Invalid path", 403
    if not os.path.exists(safe_path):
        return "Not found", 404
    from flask import send_from_directory
    return send_from_directory(image_dir, filename)


@main_bp.route('/api/plugin_order', methods=['POST'])
def save_plugin_order():
    """Save the custom plugin order."""
    device_config = current_app.config['DEVICE_CONFIG']

    data = request.get_json() or {}
    order = data.get('order', [])

    if not isinstance(order, list):
        return jsonify({"error": "Order must be a list"}), 400

    device_config.set_plugin_order(order)

    return jsonify({"success": True})