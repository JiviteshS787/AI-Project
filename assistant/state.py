def update_usage_state(model: str, key_id: str, tracker):
    snap = tracker.snapshot(model, key_id)
    state["stats"].setdefault(model, {})[key_id] = {
        "tpm_used": snap["tpm"][0], "tpm_limit": snap["tpm"][1],
        "tpd_used": snap["tpd"][0], "tpd_limit": snap["tpd"][1],
        "rpm_used": snap["rpm"][0], "rpm_limit": snap["rpm"][1],
        "rpd_used": snap["rpd"][0], "rpd_limit": snap["rpd"][1],
    }
    state["weekly_stats"].setdefault(model, {})[key_id] = {
        "weekly_tokens": snap["weekly_tokens"],
        "weekly_calls": snap["weekly_calls"]
    }

state = {
    "last_input": None,
    "last_interpretation": None,
    "stats": {},
    "weekly_stats": {},
    "aliases": None,
    "last_alias_update": None,
    "history": [],
    "daily_summary": {},
    "weekly_summary": {},
    "active_key": None
}