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
import time
from datetime import datetime
from pathlib import Path

USAGE_FILE = Path(__file__).parent / ".groq_usage.json"

# Fallback known limits per model (from Groq's free-tier dashboard).
# RPD/TPM will be overridden live from response headers when available.
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


class UsageTracker:
    def __init__(self, path: Path = USAGE_FILE):
        self.path = path
        self._data = self._load()

    def reload(self):
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save(self):
        self.path.write_text(json.dumps(self._data, indent=2))

    def _model_bucket(self, model: str) -> dict:
        bucket = self._data.setdefault(model, {})
        if bucket.get("date") != _today():
            # New day -> reset daily counters, keep limits/live header data.
            bucket["date"] = _today()
            bucket["tokens_today"] = 0
            bucket["requests_today"] = 0
        bucket.setdefault("tokens_today", 0)
        bucket.setdefault("requests_today", 0)
        bucket.setdefault("recent_request_times", [])
        bucket.setdefault("live", {})  # last-seen header values
        return bucket

    def record(self, model: str, headers: dict | None, prompt_tokens: int, completion_tokens: int):
        """Call this after every real Groq API call."""
        bucket = self._model_bucket(model)
        total_tokens = prompt_tokens + completion_tokens

        # Local tracking (RPM window + TPD running total)
        now = time.time()
        bucket["recent_request_times"].append(now)
        bucket["recent_request_times"] = [t for t in bucket["recent_request_times"] if now - t < 60]
        bucket["requests_today"] += 1
        bucket["tokens_today"] += total_tokens

        # Live header data (authoritative for RPD + TPM)
        if headers:
            live = bucket["live"]
            for key in (
                "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests",
                "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens",
            ):
                if key in headers:
                    live[key] = headers[key]

        self._save()

    def snapshot(self, model: str) -> dict:
        """Returns {rpm: (used, limit), rpd: (used, limit), tpm: (used, limit), tpd: (used, limit)}"""
        bucket = self._model_bucket(model)
        limits = DEFAULT_LIMITS.get(model, {"rpm": 30, "rpd": None, "tpm": None, "tpd": None})
        live = bucket.get("live", {})

        now = time.time()
        rpm_used = len([t for t in bucket["recent_request_times"] if now - t < 60])

        if "x-ratelimit-limit-requests" in live:
            rpd_limit = int(live["x-ratelimit-limit-requests"])
            rpd_used = rpd_limit - int(live.get("x-ratelimit-remaining-requests", rpd_limit))
        else:
            rpd_limit = limits.get("rpd")
            rpd_used = bucket["requests_today"]

        if "x-ratelimit-limit-tokens" in live:
            tpm_limit = int(live["x-ratelimit-limit-tokens"])
            tpm_used = tpm_limit - int(live.get("x-ratelimit-remaining-tokens", tpm_limit))
        else:
            tpm_limit = limits.get("tpm")
            tpm_used = None  # no reliable per-minute local estimate without header data

        tpd_limit = limits.get("tpd")
        tpd_used = bucket["tokens_today"]

        return {
            "rpm": (rpm_used, limits.get("rpm")),
            "rpd": (rpd_used, rpd_limit),
            "tpm": (tpm_used, tpm_limit),
            "tpd": (tpd_used, tpd_limit),
        }

    def tracked_models(self) -> list[str]:
        return list(self._data.keys())