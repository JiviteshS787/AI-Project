"""
Tracks Groq rate-limit usage across RPM, RPD, TPM, TPD.

Groq's response headers only expose two of these live:
  x-ratelimit-remaining-requests / -limit-requests  -> RPD
  x-ratelimit-remaining-tokens   / -limit-tokens     -> TPM

RPM and TPD aren't exposed by Groq at all, so we track them ourselves:
  - RPM: rolling 60s window of request timestamps
  - TPD: running sum of tokens used today (resets at local midnight)

Usage is persisted to a small JSON file so counts survive across
separate test runs / script restarts within the same day.
"""

import json
import re
import time
from datetime import datetime, date, timedelta
from pathlib import Path

USAGE_FILE = Path(__file__).parent / ".groq_usage.json"

DEFAULT_LIMITS = {
    "llama-3.1-8b-instant":        {"rpm": 30, "rpd": 14400, "tpm": 6000,  "tpd": 500000},
    "llama-3.3-70b-versatile":     {"rpm": 30, "rpd": 1000,  "tpm": 12000, "tpd": 100000},
    "openai/gpt-oss-120b":         {"rpm": 30, "rpd": 1000,  "tpm": 8000,  "tpd": 200000},
    "openai/gpt-oss-20b":          {"rpm": 30, "rpd": 1000,  "tpm": 8000,  "tpd": 200000},
    "qwen/qwen3.6-27b":            {"rpm": 30, "rpd": 1000,  "tpm": 8000,  "tpd": 200000},
    "groq/compound":               {"rpm": 30, "rpd": 250,   "tpm": 70000, "tpd": None},
    "groq/compound-mini":          {"rpm": 30, "rpd": 250,   "tpm": 70000, "tpd": None},
}


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _current_week_id():
    dt = datetime.now()
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week}"


def _parse_reset_duration(value: str) -> float:
    """
    Parse Groq's reset-duration strings into seconds.
    Formats seen: "7.66s", "2m59.56s", "1h2m3.4s"
    """
    if not value:
        return 0.0

    pattern = r"(?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?"
    match = re.match(pattern, value.strip())
    if not match:
        return 0.0

    hours, minutes, seconds = match.groups()
    total = 0.0
    if hours:
        total += int(hours) * 3600
    if minutes:
        total += int(minutes) * 60
    if seconds:
        total += float(seconds)
    return total


class UsageTracker:
    def __init__(self, path: Path = USAGE_FILE):
        self.path = path
        self._data = self._load()


    def reload(self):
        self._data = self._load()
        self.reset_if_needed()


    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}


    def _save(self):
        self.path.write_text(json.dumps(self._data, indent=2))


    def reset_if_needed(self) -> bool:
        today = _today()
        now = time.time()
        modified = False

        for model, bucket in self._data.items():
            current_week = _current_week_id()
            if bucket.get("weekly_id") != current_week:
                bucket["weekly_id"] = current_week
                bucket["weekly_tokens"] = 0
                bucket["weekly_calls"] = 0
                modified = True

            if bucket.get("date") != today:
                bucket["date"] = today
                bucket["tokens_today"] = 0
                bucket["requests_today"] = 0
                bucket["recent_request_times"] = []
                bucket["live"] = {}
                bucket["live_captured_at"] = None
                bucket["tpm_reset_at"] = None
                modified = True
                #continue

            recent = bucket.get("recent_request_times", [])
            fresh_recent = [t for t in recent if now - t < 60]
            if len(fresh_recent) != len(recent):
                bucket["recent_request_times"] = fresh_recent
                modified = True

            # 3. Live Header Expiry — use Groq's own reset-tokens countdown
            #    instead of a flat 60s guess, when we have it.
            tpm_reset_at = bucket.get("tpm_reset_at")
            captured_at = bucket.get("live_captured_at")

            if tpm_reset_at is not None:
                if now >= tpm_reset_at:
                    if bucket.get("live"):
                        bucket["live"] = {}
                        bucket["tpm_reset_at"] = None
                        modified = True
            elif captured_at is not None and (now - captured_at) >= 60:
                # Fallback for old data captured before this fix, with no reset_at stored
                if bucket.get("live"):
                    bucket["live"] = {}
                    modified = True

        if modified:
            self._save()

        return modified


    def _bucket_key(self, model: str, key_id: str) -> str:
        return f"{model}::{key_id}"


    def _model_bucket(self, model: str, key_id: str) -> dict:
        bucket = self._data.setdefault(self._bucket_key(model, key_id), {})
        '''
        if bucket.get("date") != _today():
            bucket["date"] = _today()
            bucket["tokens_today"] = 0
            bucket["requests_today"] = 0
            bucket["live"] = {}
            bucket["live_captured_at"] = None
            bucket["tpm_reset_at"] = None
        '''
        bucket.setdefault("tokens_today", 0)
        bucket.setdefault("requests_today", 0)
        bucket.setdefault("recent_request_times", [])
        bucket.setdefault("live", {})
        bucket.setdefault("live_captured_at", None)
        bucket.setdefault("tpm_reset_at", None)
        bucket.setdefault("weekly_tokens", 0)
        bucket.setdefault("weekly_calls", 0)
        bucket.setdefault("weekly_id", _current_week_id())

        self.reset_if_needed()
        return bucket


    def record(self, model: str, key_id: str, headers: dict | None, prompt_tokens: int, completion_tokens: int):
        bucket = self._model_bucket(model, key_id)
        self.reset_if_needed()

        total_tokens = prompt_tokens + completion_tokens

        now = time.time()
        bucket["recent_request_times"].append(now)
        bucket["recent_request_times"] = [t for t in bucket["recent_request_times"] if now - t < 60]
        bucket["requests_today"] += 1
        bucket["tokens_today"] += total_tokens

        bucket["weekly_tokens"] = bucket.get("weekly_tokens", 0) + total_tokens
        bucket["weekly_calls"] = bucket.get("weekly_calls", 0) + 1

        if headers:
            live = bucket["live"]
            for key in (
                "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests",
                "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens",
                "x-ratelimit-reset-tokens", "x-ratelimit-reset-requests",
            ):
                if key in headers:
                    live[key] = headers[key]
            bucket["live_captured_at"] = now

            # Compute the absolute time TPM data actually expires, using
            # Groq's own reset-tokens countdown instead of guessing 60s.
            reset_tokens_str = headers.get("x-ratelimit-reset-tokens")
            if reset_tokens_str:
                bucket["tpm_reset_at"] = now + _parse_reset_duration(reset_tokens_str)
            else:
                bucket["tpm_reset_at"] = None

        self._save()


    def snapshot(self, model: str, key_id: str) -> dict:
        bucket = self._model_bucket(model, key_id)
        limits = DEFAULT_LIMITS.get(model, {"rpm": 30, "rpd": None, "tpm": None, "tpd": None})
        live = bucket.get("live", {})
        captured_at = bucket.get("live_captured_at")
        tpm_reset_at = bucket.get("tpm_reset_at")
        now = time.time()

        rpm_used = len([t for t in bucket["recent_request_times"] if now - t < 60])

        rpd_live_valid = captured_at is not None and datetime.fromtimestamp(captured_at).strftime("%Y-%m-%d") == _today()
        if rpd_live_valid and "x-ratelimit-limit-requests" in live:
            rpd_limit = int(live["x-ratelimit-limit-requests"])
        else:
            rpd_limit = limits.get("rpd")
        rpd_used = bucket["requests_today"]

        # TPM live data is valid until Groq's own reset countdown expires
        if tpm_reset_at is not None:
            tpm_live_valid = now < tpm_reset_at
        else:
            tpm_live_valid = captured_at is not None and (now - captured_at) < 60

        if tpm_live_valid and "x-ratelimit-limit-tokens" in live:
            tpm_limit = int(live["x-ratelimit-limit-tokens"])
            tpm_used = tpm_limit - int(live.get("x-ratelimit-remaining-tokens", tpm_limit))
        else:
            tpm_limit = limits.get("tpm")
            tpm_used = 0

        tpd_limit = limits.get("tpd")
        tpd_used = bucket["tokens_today"]

        return {
            "rpm": (rpm_used, limits.get("rpm")),
            "rpd": (rpd_used, rpd_limit),
            "tpm": (tpm_used, tpm_limit),
            "tpd": (tpd_used, tpd_limit),
            "weekly_tokens": bucket.get("weekly_tokens", 0), 
            "weekly_calls": bucket.get("weekly_calls", 0)
        }


    def tracked_models(self) -> list[str]:
        return list(self._data.keys())