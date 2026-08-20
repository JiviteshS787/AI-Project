from assistant.monitor.usage_tracker import UsageTracker

tracker = UsageTracker()

def update_usage_state(model: str):
    snap = tracker.snapshot(model)
    state["stats"][model] = {
        "tpm_used": snap["tpm"][0], "tpm_limit": snap["tpm"][1],
        "tpd_used": snap["tpd"][0], "tpd_limit": snap["tpd"][1],
        "rpm_used": snap["rpm"][0], "rpm_limit": snap["rpm"][1],
        "rpd_used": snap["rpd"][0], "rpd_limit": snap["rpd"][1],
    }

state = {
    "last_input": None,
    "last_interpretation": None,
    "stats": {
        "tpm": 0,
        "tpd": 0,
        "rpm": 0,
        "rpd": 0
    }
}