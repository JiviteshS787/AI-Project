def format_command(command):
    action = command["action"]
    target = command.get("target")
    parameters = command.get("parameters", {})

    # Capitalize target nicely
    target_text = target.title() if target else ""

    if action == "open":
        text = f"Opening {target_text}"

        if "websites" in parameters:
            sites = [
                site.replace(".com", "").title()
                for site in parameters["websites"]
            ]
            if parameters["websites"]:
                text += " with " + ", ".join(sites)

        return text

    if action == "close_app":
        return f"Closing {target_text}"

    if action == "start_project":
        return f"Starting project {target_text}"

    if action == "stop_project":
        return f"Stopping project {target_text}"

    if action == "run_script":
        return f"Running script {target_text}"

    if action == "list_running_processes":
        return "Listing running processes"

    if action == "show_history":
        return "Showing history"

    if action == "delete_history":
        return "Deleting history"

    return f"{action} {target_text}"

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