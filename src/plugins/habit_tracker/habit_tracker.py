"""habit_tracker.py — Habit Tracker plugin for InkyPi.

Renders a daily habit grid showing streaks and today's completion status.
All habit data is stored in the plugin instance settings — no external services needed.
"""

import json
import logging
from datetime import date, timedelta

from plugins.base_plugin.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

STREAK_DAYS = 14  # How many past days to show in the grid


class HabitTracker(BasePlugin):
    """Displays a habit tracker with streak counts and a completion grid."""

    def generate_settings_template(self):
        params = super().generate_settings_template()
        params["settings_template"] = "habit_tracker/settings.html"
        params["style_settings"] = True
        return params

    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        habits = self._parse_habits(settings)
        today = date.today()

        habit_rows = []
        for habit in habits:
            streak = self._calculate_streak(habit["completions"], today)
            # Build grid: last STREAK_DAYS days (oldest → newest)
            grid = []
            for i in range(STREAK_DAYS - 1, -1, -1):
                day = today - timedelta(days=i)
                grid.append({
                    "date": day.isoformat(),
                    "done": day.isoformat() in habit["completions"],
                    "is_today": i == 0,
                })
            habit_rows.append({
                "name": habit["name"],
                "streak": streak,
                "grid": grid,
            })

        template_params = {
            "habits": habit_rows,
            "today": today.strftime("%A, %B %-d"),
            "plugin_settings": settings,
        }

        return self.render_image(
            dimensions, "habit_tracker.html", "habit_tracker.css", template_params
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_habits(self, settings: dict) -> list:
        """Parse the habits_data JSON from settings into a list of dicts."""
        raw = settings.get("habits_data", "[]")
        try:
            habits = json.loads(raw) if isinstance(raw, str) else raw
            return [h for h in habits if isinstance(h, dict) and h.get("name")]
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not parse habits_data JSON; returning empty list.")
            return []

    def _calculate_streak(self, completions: list, today: date) -> int:
        """Return the current consecutive-day streak ending today (or yesterday)."""
        if not completions:
            return 0

        completion_dates = set()
        for c in completions:
            try:
                completion_dates.add(date.fromisoformat(c))
            except ValueError:
                pass

        streak = 0
        # Start counting from today; if today not done, start from yesterday
        check = today if today in completion_dates else today - timedelta(days=1)
        while check in completion_dates:
            streak += 1
            check -= timedelta(days=1)
        return streak
