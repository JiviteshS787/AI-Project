from assistant.tools import open_app, run_project, run_script, stop_project, list_running_projects

def execute(function): #function is a JSON obj, action and value are the attributes of said obj
    '''
    What to use to complete the given function
    '''
    action = function["action"]

    if action == 'open_app':
        open_app(function["value"])
    elif action == 'run_project':
        run_project(function["value"])
    elif action == 'run_script':
        run_script(function["value"])
    elif action == 'stop_project':
        stop_project(function["value"])
    elif action == 'list running processes':
        list_running_projects()
    else:
        print("Unknown action")

