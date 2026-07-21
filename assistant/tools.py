import subprocess, json, os
from assistant.process_manager import start_process, stop_process, list_process

#Load in json files
with open("data/apps.json") as file:
    apps = json.load(file)

with open("data/projects.json") as file:
    projects = json.load(file)

def open_app(app_name, parameters = None):
    '''
    Open an app
    '''
    if app_name in apps:

        command = [apps[app_name]]

        if parameters:
            if "website" in parameters:
                command.append(parameters["website"])

        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        print(f"Unknown application: {app_name}")


def run_script(script_name):
    '''
    Run python files
    '''
    if script_name in projects:

        script = projects[script_name]

        python_path = script["python"]
        file_path = script["file"]
        working_dir = os.path.dirname(file_path)

        subprocess.run([python_path, file_path], cwd = working_dir)
    else:
        print("Project not found")


def run_project(project_name, parameters = "None"):
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
    else:
        print("Project not found")


def stop_project(name, parameters = "None"):
    stop_process(name)


def list_running_projects():
    list_process()