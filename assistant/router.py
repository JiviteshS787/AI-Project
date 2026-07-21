from assistant.tools import open_app, run_project, run_script, stop_project, list_running_projects
from assistant.memory import load_memory, save_memory

def execute(function): #function is a JSON obj, action and target are the attributes of said obj
    '''
    What to use to complete the given function
    '''
    action = function["action"]
    memory = load_memory()

    if action == 'open_app':
        open_app(function["target"], function.get("parameters"))

        #Updating memory with app opened
        memory["last_app"] = function["target"]
        memory["app_params"] = function.get("parameters") or {}
        memory["last_action"] = "open_app" #Make sure you know the most recent action
        save_memory(memory)

    elif action == 'run_project':
        run_project(function["target"], function.get("parameters"))

        #Updating memory with project opened\
        memory["last_project"] = function["target"]
        memory["project_params"] = function.get("parameters") or {}
        memory["last_action"] = "run_project" #Make sure you know the most recent action
        save_memory(memory)

    elif action == 'run_script':
        run_script(function["target"])

    elif action == 'stop_project':
        stop_project(function["target"], function.get("parameters"))

        #Latest project stopped
        memory["last_project"] = function["target"]
        memory["last_action"] = "stop_project"
        save_memory(memory)

    elif action == 'list_running_processes':
        list_running_projects()

    else:
        print("Unknown action")

