import json
from difflib import get_close_matches

from assistant.router import execute

from assistant.command_decipher import decipher
from assistant.command_parser import split_commands
from assistant.confirmation import confirm_command

with open("data/apps.json", "r") as file:
    apps = json.load(file)

with open("data/files.json", "r") as file:
    files = json.load(file)

openables = {**apps, **files}


while True:
    print("> ", end="", flush=True)
    user_input = input().lower().strip()

    if user_input == 'help':
        # What commands are there to call?
        print("Available commands:")
        print("- open <app/file>")
        print("- close <app/file>")
        print("- start <project>")
        print("- stop <project>")
        print("- run <script>")
        print("- history")
        print("- end")
        print("\n")

    elif user_input == 'end':
        break

    else:
        #i = 1
        all_commands = []
        commands = split_commands(user_input)
        #print(commands)
        for entry in commands:
            command = decipher(entry)
            #print(f"Command #{i}: {command}")
            #i+=1

            if command:
                if isinstance(command, list):
                    all_commands.extend(command)
                else:
                    all_commands.append(command)
            else:
                matches = get_close_matches(entry, list(openables.keys()), n=3, cutoff=0.6)

                if matches:
                    print("Command not found. Did you mean:")
                    for match in matches:
                        print(f"- {match}")
                else:
                    print(f"Command not found: {entry}")

        #Confirm together
        if all_commands:
            if confirm_command(all_commands):
                for cmd in all_commands:
                    execute(cmd)
    
    #print("\n")


'''
> open chrome with youtube, netflix and disney, claculator and documents

=== Ready to Execute ===
1. Opening Chrome with Youtube, Netflix, Disney, Claculator
2. Opening Documents

Add fuzzy spell check to possible_item check


Check the spacing in displayed history, tweak how parameters are displayed
'''
        