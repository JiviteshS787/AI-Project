import os
import ctypes

def sleep_system():
    print("Sleeping...")
    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)

def lock_system():
    print("Locking screen...")
    ctypes.windll.user32.LockWorkStation()

def restart_system():
    print("Restarting...")
    os.system("shutdown /r /t 0")

def shutdown_system():
    print("Shutting down...")
    os.system("shutdown /s /t 0")