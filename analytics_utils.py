# analytics_utils.py
from typing import Optional
import pandas as pd

import db

def _safe_usage_summary(user_id: Optional[str]):
    """
    Gracefully handle deployments where db.usage_summary doesn't exist
    or raises an error (e.g., logging disabled / older db.py).
    """
    fn = getattr(db, "usage_summary", None)
    if callable(fn):
        try:
            return fn(user_id=user_id)
        except Exception:
            pass
    # Fallback empty shape the UI can render against
    return {"totals": {}, "by_day": [], "by_model": []}

def build_analytics_frames(user_id: Optional[str]):
    data = _safe_usage_summary(user_id=user_id)
    totals = data.get("totals", {}) or {}

    by_day = pd.DataFrame(data.get("by_day", []))
    by_model = pd.DataFrame(data.get("by_model", []))

    if not by_day.empty:
        by_day["day"] = pd.to_datetime(by_day["day"])
        by_day = by_day.sort_values("day")
        by_day["tokens"] = by_day["tokens_in"].fillna(0) + by_day["tokens_out"].fillna(0)

    if not by_model.empty:
        by_model["tokens"] = by_model["tokens"].fillna(0)
        by_model = by_model.sort_values("cost", ascending=False)

    return totals, by_day, by_model
