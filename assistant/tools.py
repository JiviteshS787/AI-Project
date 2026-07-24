import subprocess, json, os
from assistant.process_manager import start_process, stop_process, list_process
from assistant.app_manager import open_app as launch_app, close_app as terminate_app

#Load in json files
with open("data/apps.json") as file:
    apps = json.load(file)

with open("data/projects.json") as file:
    projects = json.load(file)

with open("data/scripts.json", "r") as file:
    scripts = json.load(file)


def open_app(app_name, parameters=None):
    '''
    Open an app
    '''
    if app_name in apps:

        command = [apps[app_name]["path"]]

        if parameters:
            if "websites" in parameters:
                for website in parameters["websites"]:
                    command.append(website)

        return launch_app(command, app_name)

    else:
        print(f"Unknown application: {app_name}")
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


def list_running_projects():
    list_process()