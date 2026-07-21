import subprocess

running_processes =  {}

def start_process(name, command, cwd = None):
    if name in running_processes:
        print(f'{name} => already running')
        return
    
    execute = subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) #mostly for py projects that run in the background
     
    running_processes[name] = execute

    print(f'{name} => started \n')


def stop_process(name):
    if name in running_processes:
        stop = running_processes[name]
        stop.terminate() #stop process

        del running_processes[name]
        
        print(f'{name} => terminated \n')
    else:
        print(f'{name} => not running \n')


def list_process():

    # Remove processes that have ended
    finished = []

    for name, process in running_processes.items():
        if process.poll() is not None:
            finished.append(name)

    for name in finished:
        del running_processes[name]


    if len(running_processes) == 0:
        print("No running processes")

    else:
        print(f"{len(running_processes)} process(es) running:")

        for name in running_processes.keys():
            print(f"- {name}")

    print("\n")


