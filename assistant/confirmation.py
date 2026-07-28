def format_command(command):
    action = command["action"]
    target = command.get("target")
    parameters = command.get("parameters", {})

    text = f"{action.replace('_', ' ')} {target}"

    if parameters:
        if "websites" in parameters:
            text += " with " + ", ".join(parameters["websites"])

    return text

def confirm_command(commands):
    if not isinstance(commands, list):
        commands = [commands]

    print("\nConfirm:")
    
    for command in commands:
        print("-", format_command(command))

    answer = input("> ").lower()

    return answer in ["yes", "y", "confirm"]