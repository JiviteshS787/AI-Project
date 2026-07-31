confirmations = {
    "open": "Opening",
    "close": "Closing",
    "start_project": "Starting project",
    "stop_project": "Stopping project",
    "run_script": "Running script",
    "list_running_processes": "Listed running processes",
    "show_history": "Showing history",
    "delete_history": "Clearing history",
    "delete_alias": "Deleting alias",
    "create_alias": "Creating alias",
    "list_aliases": "Listing aliases"
}


def format_command(command):
    action = command.get("action")
    target = command.get("target", "")
    parameters = command.get("parameters", {})

    target_text = target.title() if target else ""

    # Get the action phrase
    action_text = confirmations.get(action, action)

    # Open with websites
    if action == "open":
        text = f"{action_text} {target_text}"
        websites = parameters.get("websites", [])

        if websites:
            sites = [
                site.replace(".com", "").title()
                for site in websites
            ]
            text += " with " + ", ".join(sites)

        return text

    if action in ["create_alias", "delete_alias"]:
        alias_target = parameters.get("alias_for", "")
        alias_target = alias_target.title()

        return f"{action_text} {target_text} -> {alias_target}"

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