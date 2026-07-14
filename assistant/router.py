from assistant.tools import open_app, run_file

def execute(function): #function is a JSON obj, action and value are the attributes of said obj
    '''
    What to use to complete the given function
    '''
    
    action = function["action"]

    if action == 'open_app':
        open_app(function["value"])
    elif action == 'run_file':
        run_file(function["value"])
    else:
        print("Unknown action")

