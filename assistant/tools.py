import subprocess

def open_app(app_name):
    '''
    Open an app
    '''
    if app_name == "chrome":
        subprocess.Popen(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
    elif app_name == "calculator":
        subprocess.Popen("calc")
    else:
        print(f"Unknown application: {app_name}")