import subprocess, psutil, json, os

PROCESS_FILE = "data/processes.json"

running_processes = {}


def start_process(name, command, cwd=None):

    clean_processes()

    if name in running_processes:
        print(f"{name} => already running")
        return False

    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    pid = process.pid

    print(f"{name} launcher PID: {pid}")

    running_processes[name] = {"pid": pid, "command": command}  

    save_processes()

    print(f"{name} => started\n")
    return True


def stop_process(name):

    clean_processes()

    if name not in running_processes:
        print(f"{name} => not running\n")
        return False

    pid = running_processes[name]["pid"]

    try:
        parent = psutil.Process(pid)
        processes = [parent]
        # Include children
        processes += parent.children(recursive=True)


        for process in processes:
            try:
                print(f"Killing {process.name()} {process.pid}")
                process.kill()

            except psutil.NoSuchProcess:
                pass

        del running_processes[name]
        save_processes()

        print(f"{name} => terminated\n")
        return True


    except psutil.NoSuchProcess:
        del running_processes[name]
        save_processes()
        print(f"{name} => already closed\n")
        return False


    except psutil.AccessDenied:
        print(f"{name} => permission denied\n")
        return False


def list_running_processes():

    clean_processes()

    if not running_processes:
        print("No running processes\n")
        return

    print(f"{len(running_processes)} process(es) running:")

    for name, data in running_processes.items():
        print(f"- {name} (PID: {data['pid']})")

    print()


def load_processes():
    if not os.path.exists(PROCESS_FILE):
        return {}

    with open(PROCESS_FILE, "r") as file:
        return json.load(file)


def save_processes():
    with open(PROCESS_FILE, "w") as file:
        json.dump(running_processes, file, indent=4)


def clean_processes():
    finished = []

    for name, data in running_processes.items():
        pid = data["pid"]

        if not psutil.pid_exists(pid):
            finished.append(name)

    for name in finished:
        del running_processes[name]

    if finished:
        save_processes()


running_processes = load_processes()
clean_processes()