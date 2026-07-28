import json
from difflib import get_close_matches

from assistant.router import execute

from assistant.command_decipher import decipher
from assistant.command_parser import split_commands
from assistant.confirmation import confirm_command

with open("data/commands.json", "r") as file:
    functions = json.load(file) #Converts JSON to py dict

while True:
    print("> ", end="", flush=True)
    user_input = input().lower().strip()

    if user_input in functions:
        if confirm_command(functions[user_input]):
            execute(functions[user_input])
        else:
            print("Cancelled.\n")

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
        #i = 1
        commands = split_commands(user_input)
        print(commands)
        for entry in commands:
            command = decipher(entry)
            #print(f"Command #{i}: {command}")
            #i+=1
            
            if command:
                if confirm_command(command):
                    if isinstance(command, list):
                        for cmd in command:
                            execute(cmd)

                    else:
                        execute(command)
                else:
                    print("Cancelled.\n")

                #execute(command)
            else:
                matches = get_close_matches(entry, functions.keys(), n=3, cutoff=0.6) #Checks for close matches of commands, not exact

                if matches:
                    print("Command not found. Did you mean:")
                    for match in matches:
                        print(f"- {match}")
                else:
                    print(f"Command not found: {entry}")
            


        