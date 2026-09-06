import os
import ctypes
import win32ts
import win32process
import win32con
import win32security
import subprocess

def sleep_system():
    print("Sleeping...")
    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)


def lock_system():
    print("Locking screen...")
    try:
        sessions = win32ts.WTSEnumerateSessions()
        active_session_id = None
        for session in sessions:
            if session['State'] == win32ts.WTSActive:
                active_session_id = session['SessionId']
                break

        if active_session_id is None:
            print("No active session found — cannot lock.")
            return

        user_token = win32ts.WTSQueryUserToken(active_session_id)

        startup_info = win32process.STARTUPINFO()
        startup_info.lpDesktop = "winsta0\\default"

        win32process.CreateProcessAsUser(
            user_token,
            None,
            "rundll32.exe user32.dll,LockWorkStation",
            None,
            None,
            False,
            win32con.NORMAL_PRIORITY_CLASS,
            None,
            None,
            startup_info
        )
        print("Lock command sent to active session.")
    except Exception as e:
        print(f"Lock failed: {e}")


def restart_system():
    print("Restarting...")
    subprocess.run(["shutdown", "/r", "/t", "0"], check=True)


def shutdown_system():
    print("Shutting down...")
    subprocess.run(["shutdown", "/s", "/t", "0"], check=True)