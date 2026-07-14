import subprocess, json

#Load in json files
with open("data/apps.json") as file:
    apps = json.load(file)

with open("data/projects.json") as file:
    projects = json.load(file)

def open_app(app_name):
    '''
    Open an app
    '''
    if app_name in apps:
        subprocess.Popen(apps[app_name])
    else:
        print(f"Unknwon application: {app_name}")

    '''
    if app_name == "chrome":
        subprocess.Popen(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
    elif app_name == "calculator":
        subprocess.Popen("calc")
    else:
        print(f"Unknown application: {app_name}")
    '''

def run_file(project_name):
    '''
    Run python files
    '''
    if project_name in projects:
        subprocess.Popen(["python", projects[project_name]])
    else:
        print("Project not found")
