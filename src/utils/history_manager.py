"""history_manager.py — Manages a rolling log of display history entries."""

import json
import logging
import os
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_HISTORY_ENTRIES = 50
HISTORY_FILE = "display_history.json"
HISTORY_IMAGE_DIR = "history"


class HistoryManager:
    """Maintains a rolling log of what has been shown on the display.

    Each entry records the plugin, timestamp, and a thumbnail copy of the image
    that was shown. Entries are capped at MAX_HISTORY_ENTRIES.
    """

    def __init__(self, base_dir: str):
        """
        Args:
            base_dir: Absolute path to the ``static/images`` directory where
                      plugin images and the current_image.png are stored.
        """
        self.base_dir = base_dir
        self.history_file = os.path.join(base_dir, HISTORY_FILE)
        self.image_dir = os.path.join(base_dir, HISTORY_IMAGE_DIR)
        os.makedirs(self.image_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_entry(self, refresh_info: dict, current_image_path: str) -> None:
        """Append a new history entry and prune old ones.

        Args:
            refresh_info: Dictionary with keys: refresh_time, plugin_id,
                          refresh_type, and optionally playlist / plugin_instance.
            current_image_path: Absolute path to the image that was just shown.
        """
        entries = self._load()

        timestamp = refresh_info.get("refresh_time", datetime.utcnow().isoformat())
        # Build a safe filename from the timestamp
        safe_ts = timestamp.replace(":", "-").replace("+", "_")
        thumb_filename = f"history_{safe_ts}.png"
        thumb_path = os.path.join(self.image_dir, thumb_filename)

        # Copy the displayed image as thumbnail
        if current_image_path and os.path.exists(current_image_path):
            try:
                shutil.copy2(current_image_path, thumb_path)
            except Exception as e:
                logger.warning(f"Could not save history thumbnail: {e}")
                thumb_filename = None
        else:
            thumb_filename = None

        entry = {
            "timestamp": timestamp,
            "plugin_id": refresh_info.get("plugin_id"),
            "refresh_type": refresh_info.get("refresh_type"),
            "playlist": refresh_info.get("playlist"),
            "plugin_instance": refresh_info.get("plugin_instance"),
            "thumbnail": thumb_filename,
        }

        entries.insert(0, entry)  # newest first

        # Prune old entries (file + record)
        while len(entries) > MAX_HISTORY_ENTRIES:
            removed = entries.pop()
            self._delete_thumbnail(removed.get("thumbnail"))

        self._save(entries)

    def get_entries(self) -> list:
        """Return all history entries, newest first."""
        return self._load()

    def clear(self) -> None:
        """Delete all history entries and their thumbnail images."""
        entries = self._load()
        for entry in entries:
            self._delete_thumbnail(entry.get("thumbnail"))
        self._save([])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> list:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read history file: {e}")
            return []

    def _save(self, entries: list) -> None:
        try:
            with open(self.history_file, "w") as f:
                json.dump(entries, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not write history file: {e}")

    def _delete_thumbnail(self, filename: str) -> None:
        if not filename:
            return
        path = os.path.join(self.image_dir, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.warning(f"Could not delete history thumbnail {path}: {e}")
