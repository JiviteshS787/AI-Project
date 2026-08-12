"""
Live terminal dashboard for Groq rate-limit usage.

Run this in a separate terminal while your tests run:
    python -m assistant.monitor.rate_monitor

It just polls the shared usage file — it never calls the Groq API itself.
"""

import time

from rich.live import Live
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn

from assistant.monitor.usage_tracker import UsageTracker, DEFAULT_LIMITS


def _bar(used, limit, width=30) -> str:
    if used is None:
        return "[dim]no data yet[/dim]"
    if not limit:
        return f"{used} (no known limit)"
    pct = min(used / limit, 1.0)
    filled = int(pct * width)
    color = "green" if pct < 0.7 else "yellow" if pct < 0.9 else "red"
    bar = f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}]"
    return f"{bar} {used}/{limit} ({pct*100:.0f}%)"


def render(tracker: UsageTracker) -> Table:
    table = Table(title="Groq Rate Limit Usage", expand=True)
    table.add_column("Model", style="bold cyan")
    table.add_column("RPM")
    table.add_column("RPD")
    table.add_column("TPM")
    table.add_column("TPD")

    models = tracker.tracked_models() or list(DEFAULT_LIMITS.keys())
    for model in models:
        snap = tracker.snapshot(model)
        table.add_row(
            model,
            _bar(*snap["rpm"]),
            _bar(*snap["rpd"]),
            _bar(*snap["tpm"]),
            _bar(*snap["tpd"]),
        )
    return table


def main():
    tracker = UsageTracker()
    with Live(render(tracker), refresh_per_second=2) as live:
        while True:
            time.sleep(0.5)
            tracker.reload()          # <-- pick up whatever the test suite just wrote
            live.update(render(tracker))


if __name__ == "__main__":
    main()