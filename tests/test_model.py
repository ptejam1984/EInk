import pytest
from datetime import datetime

import pytz

from src.model import Playlist, ALL_DAYS


def make_dt(time_str, day_name="Mon", tz=pytz.UTC):
    """Build a timezone-aware datetime for the given HH:MM and weekday name."""
    # Map abbreviated day names to ISO weekday numbers (Mon=0 ... Sun=6)
    day_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    # Use a fixed Monday as the anchor (2024-01-01 is a Monday)
    anchor_monday = datetime(2024, 1, 1, tzinfo=tz)
    target_day = day_map[day_name]
    offset_days = target_day  # Mon=0 offset
    if time_str == "24:00":
        # Treat 24:00 as the start of the next day
        dt = anchor_monday.replace(hour=0, minute=0) + __import__('datetime').timedelta(days=offset_days + 1)
    else:
        h, m = map(int, time_str.split(":"))
        dt = anchor_monday.replace(hour=h, minute=m) + __import__('datetime').timedelta(days=offset_days)
    return dt


class TestPlaylist:

    @pytest.mark.parametrize(
        "start,end,current,expected,priority",
        [
            # --- Non-wrapping cases 09:00 <-> 15:00 ---
            ("09:00", "15:00", "08:59", False, 360),  # just before start
            ("09:00", "15:00", "09:00", True, 360),   # exactly at start
            ("09:00", "15:00", "12:00", True, 360),   # during
            ("09:00", "15:00", "14:59", True, 360),   # just before end
            ("09:00", "15:00", "15:00", False, 360),  # exactly at end
            ("09:00", "15:00", "23:00", False, 360),  # way after

            # --- Wrapping cases (crossing midnight) 21:00 <-> 03:00 ---
            ("21:00", "03:00", "20:59", False, 360),  # just before start
            ("21:00", "03:00", "21:00", True, 360),   # exactly at start
            ("21:00", "03:00", "23:59", True, 360),   # before midnight
            ("21:00", "03:00", "00:00", True, 360),   # after midnight, inside
            ("21:00", "03:00", "02:59", True, 360),   # just before end
            ("21:00", "03:00", "03:00", False, 360),  # exactly at end
            ("21:00", "03:00", "11:00", False, 360),  # way after

            # --- Equal start and end 12:00 <-> 12:00 ---
            ("12:00", "12:00", "11:59", False, 0),
            ("12:00", "12:00", "12:00", False, 0),
            ("12:00", "12:00", "12:01", False, 0),

            # --- Midnight boundaries 18:00 <-> 00:00 ---
            ("18:00", "00:00", "17:59", False, 360),  # before start
            ("18:00", "00:00", "23:59", True, 360),   # before end
            ("18:00", "00:00", "00:00", False, 360),  # exactly at end

            # --- Midnight boundaries 00:00 <-> 06:00 ---
            ("00:00", "06:00", "00:00", True, 360),   # start at midnight
            ("00:00", "06:00", "05:59", True, 360),   # before end
            ("00:00", "06:00", "06:00", False, 360),  # exactly at end

            # --- All day 00:00 <-> 24:00 ---
            ("00:00", "24:00", "00:00", True, 1440),   # exactly at start
            ("00:00", "24:00", "10:00", True, 1440),   # during
            ("00:00", "24:00", "23:59", True, 1440),   # just before end
            # Note: "24:00" as a *current* time is impossible with real datetimes;
            # it only existed as a string-comparison artefact in the old code.
        ]
    )
    def test_is_active_and_priority(self, start, end, current, expected, priority):
        playlist = Playlist("Test Playlist", start, end)
        dt = make_dt(current, day_name="Mon")  # Use Monday (always active by default)
        assert playlist.is_active(dt) == expected
        assert playlist.get_priority() == priority

    @pytest.mark.parametrize(
        "days,day_name,expected",
        [
            # All days active (default)
            (None,                              "Mon", True),
            (None,                              "Sat", True),
            # Weekdays only
            (["Mon","Tue","Wed","Thu","Fri"],   "Mon", True),
            (["Mon","Tue","Wed","Thu","Fri"],   "Fri", True),
            (["Mon","Tue","Wed","Thu","Fri"],   "Sat", False),
            (["Mon","Tue","Wed","Thu","Fri"],   "Sun", False),
            # Weekends only
            (["Sat","Sun"],                     "Sat", True),
            (["Sat","Sun"],                     "Sun", True),
            (["Sat","Sun"],                     "Mon", False),
            # Single day
            (["Wed"],                           "Wed", True),
            (["Wed"],                           "Thu", False),
        ]
    )
    def test_is_active_day_of_week(self, days, day_name, expected):
        # Use a time window that covers midday to avoid interference
        playlist = Playlist("Test Playlist", "09:00", "17:00", days=days)
        dt = make_dt("12:00", day_name=day_name)
        assert playlist.is_active(dt) == expected

    def test_days_default_all(self):
        """A playlist with no days specified should be active every day."""
        p = Playlist("P", "00:00", "24:00")
        assert p.days == ALL_DAYS

    def test_to_dict_includes_days(self):
        p = Playlist("P", "09:00", "17:00", days=["Mon", "Fri"])
        d = p.to_dict()
        assert d["days"] == ["Mon", "Fri"]

    def test_from_dict_restores_days(self):
        data = {
            "name": "P", "start_time": "09:00", "end_time": "17:00",
            "plugins": [], "days": ["Sat", "Sun"]
        }
        p = Playlist.from_dict(data)
        assert p.days == ["Sat", "Sun"]

    def test_from_dict_no_days_defaults_to_all(self):
        """Backward compatibility: existing configs without 'days' should default to all days."""
        data = {
            "name": "P", "start_time": "09:00", "end_time": "17:00",
            "plugins": []
        }
        p = Playlist.from_dict(data)
        assert p.days == ALL_DAYS
        