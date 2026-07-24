import subprocess, psutil

running_processes = {}


def start_process(name, command, cwd=None):

    if name in running_processes:
        print(f"{name} => already running")
        return False

    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    pid = process.pid

    print(f"{name} launcher PID: {pid}")

    try:
        parent = psutil.Process(pid)
        # Give app time to spawn real process
        parent.wait(timeout=0.5)

    except:
        pass

    running_processes[name] = pid
    print(f"{name} => started\n")
    return True


def stop_process(name):

    if name not in running_processes:
        print(f"{name} => not running\n")
        return False

    pid = running_processes[name]

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
        print(f"{name} => terminated\n")
        return True


    except psutil.NoSuchProcess:
        del running_processes[name]
        print(f"{name} => already closed\n")
        return False


    except psutil.AccessDenied:
        print(f"{name} => permission denied\n")
        return False


def list_process():

    finished = []

    for name, pid in running_processes.items():
        if not psutil.pid_exists(pid):
            finished.append(name)

    for name in finished:
        del running_processes[name]

    if not running_processes:
        print("No running processes")

    else:
        print(f"{len(running_processes)} process(es) running:")

        for name in running_processes:
            print(f"- {name}")
    print()