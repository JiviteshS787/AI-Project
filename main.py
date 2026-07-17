import json
from assistant.router import execute
from assistant.command_decipher import decipher
from difflib import get_close_matches

with open("data/commands.json", "r") as file:
    functions = json.load(file) #Converts JSON to py dict

while True:
    print("> ", end="", flush=True)
    user_input = input().lower().strip()

    if user_input in functions:
        execute(functions[user_input])

    elif user_input == 'help':
        # What commands are there to call?
        print("Available commands:")
        for cmd in functions.keys():
            print(f"- {cmd}")
        print("- end")
        print("\n")

    elif user_input == 'end':
        break

    else:
        command = decipher(user_input)

        if command:
            execute(command)
        else:
            matches = get_close_matches(user_input, functions.keys(), n=3, cutoff=0.6) #Checks for close matches of commands, not exact

            if matches:
                print("Command not found. Did you mean:")
                for match in matches:
                    print(f"- {match}")
            else:
                print("Command not found")


        