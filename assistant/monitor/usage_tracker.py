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
            # 1. Daily Reset (if date has rolled over)
            if bucket.get("date") != today:
                bucket["date"] = today
                bucket["tokens_today"] = 0
                bucket["requests_today"] = 0
                bucket["recent_request_times"] = []
                bucket["live"] = {}
                bucket["live_captured_at"] = None
                modified = True
                continue

            # 2. RPM Rolling Window Cleanup (remove timestamps > 60s old)
            recent = bucket.get("recent_request_times", [])
            fresh_recent = [t for t in recent if now - t < 60]
            if len(fresh_recent) != len(recent):
                bucket["recent_request_times"] = fresh_recent
                modified = True

            # 3. Live Header Expiry (clear headers if captured > 60s ago)
            captured_at = bucket.get("live_captured_at")
            if captured_at is not None and (now - captured_at) >= 60:
                if bucket.get("live"):
                    bucket["live"] = {}
                    modified = True

        # Save to disk only if state actually changed
        if modified:
            self._save()

        return modified


    def _model_bucket(self, model: str) -> dict:
        bucket = self._data.setdefault(model, {})
        if bucket.get("date") != _today():
            bucket["date"] = _today()
            bucket["tokens_today"] = 0
            bucket["requests_today"] = 0
            bucket["live"] = {} 
            bucket["live_captured_at"] = None
        bucket.setdefault("tokens_today", 0)
        bucket.setdefault("requests_today", 0)
        bucket.setdefault("recent_request_times", [])
        bucket.setdefault("live", {})
        bucket.setdefault("live_captured_at", None)
        return bucket


    def record(self, model: str, headers: dict | None, prompt_tokens: int, completion_tokens: int):
        bucket = self._model_bucket(model)
        total_tokens = prompt_tokens + completion_tokens

        now = time.time()
        bucket["recent_request_times"].append(now)
        bucket["recent_request_times"] = [t for t in bucket["recent_request_times"] if now - t < 60]
        bucket["requests_today"] += 1
        bucket["tokens_today"] += total_tokens

        if headers:
            live = bucket["live"]
            for key in (
                "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests",
                "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens",
            ):
                if key in headers:
                    live[key] = headers[key]
            bucket["live_captured_at"] = now   # <-- CHANGED: stamp when this header snapshot was taken

        self._save()


    def snapshot(self, model: str) -> dict:
        bucket = self._model_bucket(model)
        limits = DEFAULT_LIMITS.get(model, {"rpm": 30, "rpd": None, "tpm": None, "tpd": None})
        live = bucket.get("live", {})
        captured_at = bucket.get("live_captured_at")
        now = time.time()

        rpm_used = len([t for t in bucket["recent_request_times"] if now - t < 60])

        # RPD is a daily limit -> live data is only valid if it was captured "today"
        # (the day-rollover reset in _model_bucket already clears it, but this guards
        # against a bucket loaded mid-flight without going through that path)
        rpd_live_valid = captured_at is not None and datetime.fromtimestamp(captured_at).strftime("%Y-%m-%d") == _today()
        if rpd_live_valid and "x-ratelimit-limit-requests" in live:
            rpd_limit = int(live["x-ratelimit-limit-requests"])
            #rpd_used = rpd_limit - int(live.get("x-ratelimit-remaining-requests", rpd_limit))
        else:
            rpd_limit = limits.get("rpd")
            #rpd_used = bucket["requests_today"]
        rpd_used = bucket["requests_today"]

        # TPM is a per-minute limit -> live data older than 60s is meaningless
        tpm_live_valid = captured_at is not None and (now - captured_at) < 60
        if tpm_live_valid and "x-ratelimit-limit-tokens" in live:
            tpm_limit = int(live["x-ratelimit-limit-tokens"])
            tpm_used = tpm_limit - int(live.get("x-ratelimit-remaining-tokens", tpm_limit))
        else:
            tpm_limit = limits.get("tpm")
            tpm_used = 0  # stale or missing -> no reliable estimate

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