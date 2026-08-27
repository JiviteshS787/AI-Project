import json

with open("data/confirmations.json", "r") as file:
    confirmations = json.load(file)


def format_command(command):
    action = command.get("action")
    target = command.get("target", "")
    parameters = command.get("parameters", {})

    target_text = target.title() if target else ""

    # Get the action phrase
    action_text = confirmations.get(action, action)

    # Open with websites / monitor
    if action == "open":
        text = f"{action_text} {target_text}"

        websites = parameters.get("websites", [])

        if websites:
            sites = [
                site.replace(".com", "").title()
                for site in websites
            ]
            text += " with " + ", ".join(sites)

        monitor = parameters.get("monitor")

        if monitor:
            text += f" on monitor {monitor}"

        return text

    if action == "create_alias":
        alias_targets = parameters.get("alias_for", "")
        aliases = alias_targets[0].title()
        for alias in alias_targets[1:]:
            aliases += "," + alias.title()

        return f"{action_text} {target_text} -> {aliases}"

    if action == "delete_alias":
        return f"{action_text} {target_text}"

    if action == "set_volume":
        volume_level = parameters.get("level")

        text = f"{action_text} to {volume_level}%"

        return text

    if action == "snap_window":
        direction = parameters.get("direction")

        text = f"{action_text} {target_text} to the {direction}"

        return text

    if action == "set_clipboard":
        copy = parameters.get("text")

        text = f"{action_text}: {copy}"

        return text

    if action == 'move_window_to_monitor':
        move = parameters.get("monitor")

        text = f"{action_text}: {target_text} to monitor {move}"

        return text

    # Actions with no target
    if not target:
        return action_text

    # Default formatting
    return f"{action_text} {target_text}"


def confirm_command(commands):
    if not isinstance(commands, list):
        commands = [commands]

    print("\n=== Ready to Execute ===")

    for i, command in enumerate(commands, 1):
        print(f"{i}. {format_command(command)}")

    print("\nOptions: [y = yes | n = cancel]")

    answer = input("> ").strip().lower()

    if answer in ["y", "yes"]:
        return True

    if answer in ["n", "no", "cancel"]:
        print("Cancelled.")
        return False

    print("Invalid input. Cancelled.")
    return False