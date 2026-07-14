import json
from assistant.router import execute

with open("data/commands.json", "r") as file:
    functions = json.load(file) #Converts JSON to py dict

'''
function_chrome = functions["open chrome"]
function_calculator = functions["open calculator"]
function_python = functions["run hello"]

execute(function_chrome)
execute(function_calculator)
execute(function_python)
'''

while True:
    user_input = input("> ")

    if user_input in functions:
        execute(functions[user_input])
    else:
        print("Command not found")