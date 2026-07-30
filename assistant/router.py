from assistant.tools import open_item, start_project, run_script, stop_project, list_processes, close_item
from assistant.memory import update_history, show_history, delete_history

def execute(function): #function is a JSON obj, action and target are the attributes of said obj
    '''
    What to use to complete the given function
    '''
    action = function["action"]

    if action == "open":
        opened = open_item(function["target"], function.get("parameters"))

        #Update memory with app/file opened
        if opened:
            update_history(function)

    elif action == "close":
        close = close_item(function["target"])

        if close:
            update_history(function)

    elif action == 'start_project':
        run = start_project(function["target"], function.get("parameters"))

        #Updating memory with project started
        if run:
            update_history(function)


    elif action == 'run_script':
        run = run_script(function["target"])

        #Updating memory with script executed
        if run:
            update_history(function)


    elif action == 'stop_project':
        stop = stop_project(function["target"], function.get("parameters"))

        #Updating memory with project stopped
        if stop:
            update_history(function)


    elif action == 'list_running_processes':
        list_processes()


    elif action == 'show_history':
        show_history()


    elif action == 'delete_history':
        delete_history()


    else:
        print("Unknown action")

