import subprocess
import psutil


def open_app(command, app_name):
    '''
    Open a normal installed application
    '''

    print(f"Command: {command}, App Name: {app_name}")

    if isinstance(command, list) and len(command) == 1 and "WindowsApps" in command[0]:
        aumid = get_aumid(app_name)
        if aumid:
            subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{aumid}"])
            print(f"{app_name} => opened via AppsFolder\n")
            return True
        else:
            print(f"No AUMID mapping found for {app_name}, cannot open\n")
            return False

    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"{app_name} => opened\n")

    return True


def get_aumid(app_name):
    '''
    Map app_name to its AppUserModelID for UWP apps
    '''
    aumid_map = {
        "outlook": "Microsoft.OutlookForWindows_8wekyb3d8bbwe!Microsoft.OutlookforWindows",
        # add more UWP apps here as needed
    }
    return aumid_map.get(app_name.lower())


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