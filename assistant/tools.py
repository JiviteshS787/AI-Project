import subprocess, json, os
from assistant.process_manager import start_process, stop_process, list_running_processes
from assistant.app_manager import open_app as launch_app, close_app as terminate_app

#Load in json files
with open("data/apps.json") as file:
    apps = json.load(file)

with open("data/projects.json") as file:
    projects = json.load(file)

with open("data/scripts.json", "r") as file:
    scripts = json.load(file)

with open("data/files.json", "r") as file:
    files = json.load(file)


openables = {**apps, **files}


def can_open_app(name):
    return name in apps


def can_open_file(name):
    return name in files


def open_file(file_name):
    if file_name in files:
        path = files[file_name]["path"]

        try:
            os.startfile(path)
            return True

        except Exception as e:
            print(f"Failed to open {file_name}: {e}")
            return False

    print(f"Unknown file: {file_name}")
    return False


def open_app(app_name, parameters=None):
    '''
    Open an app
    '''
    if app_name in apps:

        command = [apps[app_name]["path"]]

        if parameters:
            accepted = apps[app_name].get("accepted_parameters", {})

            if accepted.get("websites", False):
                for website in parameters.get("websites", []):
                    command.append(website)

        success = launch_app(command, app_name)

        if not success:
            print(f"Failed to launch {app_name}")

        return success
    else:
        print(f"Unknown application: {app_name}")
        return False


def open_item(name, parameters=None):
    '''
    Open anything (app/file)
    '''

    if name not in openables:
        print(f"Cannot find {name}")
        return False

    item_type = openables[name]["type"]

    if item_type == "app":
        return open_app(name, parameters)

    elif item_type == "file":
        return open_file(name)

    else:
        print(f"Unknown open type: {item_type}")
        return False


def close_app(app_name):
    '''
    Close an app
    '''
    if app_name in apps:
        process_name = apps[app_name]["process"]

        return terminate_app(process_name)


    print(f"Unknown application: {app_name}")
    return False


def run_script(script_name):
    '''
    Run python files
    '''
    if script_name in scripts:

        script = scripts[script_name]

        python_path = script["python"]
        file_path = script["file"]
        working_dir = os.path.dirname(file_path)

        subprocess.run([python_path, file_path], cwd = working_dir)

        return True
    else:
        print("Script not found")
        return False


def start_project(project_name, parameters = None):
    '''
    Run python projects
    '''
    if project_name in projects:

        project = projects[project_name]

        python_path = project["python"]
        file_path = project["file"]
        working_dir = os.path.dirname(file_path)

        start_process(project_name, [python_path, file_path], cwd = working_dir)

        #subprocess.Popen([python_path, file_path], cwd = working_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    else:
        print("Project not found")
        return False


def stop_project(name, parameters = None):
    if(stop_process(name)):
        return True
    return False


def list_processes():
    list_running_processes()