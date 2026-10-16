"""
PureClip Analytics & ROI Engine (Wispr Flow style)
Quantifies time saved, app switches eliminated, and links cleaned.
100% local SQLite storage.
"""

import os
import sqlite3
import datetime
from typing import Dict, Any


class MetricsTracker:
    """Tracks productivity metrics locally to demonstrate tangible user ROI."""

    def __init__(self, db_path: str = None):
        if not db_path:
            appdata = os.environ.get("LOCALAPPDATA", ".")
            data_dir = os.path.join(appdata, "PureClip")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "metrics.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date TEXT PRIMARY KEY,
                    clips_copied INTEGER DEFAULT 0,
                    clips_pasted INTEGER DEFAULT 0,
                    trackers_stripped INTEGER DEFAULT 0,
                    form_autofills INTEGER DEFAULT 0,
                    switches_avoided INTEGER DEFAULT 0,
                    seconds_saved REAL DEFAULT 0.0
                )
            """)
            conn.commit()

    def record_copy(self, trackers_count: int = 0):
        """Records a new copy event."""
        today = datetime.date.today().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_metrics (date, clips_copied, trackers_stripped)
                VALUES (?, 1, ?)
                ON CONFLICT(date) DO UPDATE SET
                    clips_copied = clips_copied + 1,
                    trackers_stripped = trackers_stripped + ?
            """, (today, trackers_count, trackers_count))
            conn.commit()

    def record_paste(self, buffer_size_at_paste: int):
        """Records a single-item paste dispatch."""
        today = datetime.date.today().isoformat()
        # If user had 3 items in buffer, using PureClip avoided (3-1) = 2 app switches
        switches_saved = max(0, min(5, buffer_size_at_paste - 1))
        time_saved = switches_saved * 4.5  # 4.5 seconds per app switch

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_metrics (date, clips_pasted, switches_avoided, seconds_saved)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    clips_pasted = clips_pasted + 1,
                    switches_avoided = switches_avoided + ?,
                    seconds_saved = seconds_saved + ?
            """, (today, switches_saved, time_saved, switches_saved, time_saved))
            conn.commit()

    def record_form_fill(self, item_count: int):
        """Records a smart Tab form cascade."""
        today = datetime.date.today().isoformat()
        switches_saved = max(0, (item_count - 1) * 2)
        time_saved = item_count * 5.0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_metrics (date, form_autofills, switches_avoided, seconds_saved)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    form_autofills = form_autofills + 1,
                    switches_avoided = switches_avoided + ?,
                    seconds_saved = seconds_saved + ?
            """, (today, switches_saved, time_saved, switches_saved, time_saved))
            conn.commit()

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregate totals for display in the insights dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    SUM(clips_copied),
                    SUM(clips_pasted),
                    SUM(trackers_stripped),
                    SUM(form_autofills),
                    SUM(switches_avoided),
                    SUM(seconds_saved),
                    COUNT(DISTINCT date)
                FROM daily_metrics
            """)
            row = cursor.fetchone()
            
            total_copied = row[0] or 0
            total_pasted = row[1] or 0
            trackers = row[2] or 0
            autofills = row[3] or 0
            switches = row[4] or 0
            total_secs = row[5] or 0.0
            active_days = row[6] or 1

            total_mins = round(total_secs / 60, 1)

            return {
                "total_copied": total_copied,
                "total_pasted": total_pasted,
                "trackers_stripped": trackers,
                "form_autofills": autofills,
                "switches_avoided": switches,
                "minutes_saved": total_mins,
                "active_days": active_days
            }
