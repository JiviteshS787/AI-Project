import subprocess
import psutil


def open_app(command, app_name):
    '''
    Open a normal installed application
    '''

    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"{app_name} => opened\n")

    return True

    
def close_app(process_name):
    '''
    Close application by process name
    '''

    if process_name.lower() == "explorer.exe":
        print("Cannot close File Explorer safely")
        print("Explorer controls the Windows desktop and taskbar\n")
        return False

    killed = False

    for process in psutil.process_iter(["pid", "name"]):
        try:
            if process.info["name"].lower() == process_name.lower():
                print(f"Killing {process.info['name']} {process.info['pid']}")

                psutil.Process(process.info["pid"]).kill()

                killed = True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        print("Application closed\n")
    else:
        print("Application not running\n")

    return killed