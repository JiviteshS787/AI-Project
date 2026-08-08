from assistant.tools import open_item, start_project, run_script, stop_project, list_processes, close_item
from assistant.alias_manager import create_alias, delete_alias, list_aliases, delete_all_aliases
from assistant.history import update_history, show_history, delete_history

from assistant.system_tools.volume import volume_up, volume_down, set_volume, mute, unmute
from assistant.system_tools.brightness import brightness_up, brightness_down, set_brightness
from assistant.system_tools.window import focus_window, minimize_window, maximize_window, snap_window


def execute(function): #function is a JSON obj, action and target are the attributes of said obj
    '''
    What to use to complete the given function
    '''
    action = function["action"]

    #######################################
    #           Opening/Closing           #
    #######################################
    if action == "open":
        opened = open_item(function["target"], function.get("parameters"))

        #Update memory with app/file opened
        if opened:
            update_history(function)

    elif action == "close":
        close = close_item(function["target"])

        if close:
            update_history(function)


    #######################################
    #           Aliases            #
    #######################################
    elif action == "create_alias":
        alias = function["target"]
        target = function["parameters"]["alias_for"]

        created = create_alias(alias, target)

        if created:
            update_history(function)

    elif action == 'delete_alias':
        deleted = delete_alias(function["target"])

        if deleted:
            update_history(function)

    elif action == 'delete_all_aliases':
        cleared = delete_all_aliases()

        if cleared:
            update_history(function)


    #######################################
    #         Proj/Script Control         #
    #######################################
    elif action == 'start_project':
        run = start_project(function["target"], function.get("parameters"))

        #Updating memory with project started
        if run:
            update_history(function)

    elif action == 'stop_project':
        stop = stop_project(function["target"], function.get("parameters"))

        #Updating memory with project stopped
        if stop:
            update_history(function)

    elif action == 'run_script':
        run = run_script(function["target"])

        #Updating memory with script executed
        if run:
            update_history(function)


    #######################################
    #           Listing/History           #
    #######################################
    elif action == 'list_running_processes':
        list_processes()

    elif action == 'list_aliases':
        list_aliases()

    elif action == 'show_history':
        show_history()

    elif action == 'delete_history':
        delete_history()

    #######################################
    #           Volume Control            #
    #######################################
    elif action == "volume_up":
        volume_up()
        update_history(function)

    elif action == "volume_down":
        volume_down()
        update_history(function)

    elif action == "mute_volume":
        mute()

    elif action == "unmute_volume":
        unmute()

    elif action == "set_volume":
        set_volume(function["parameters"]["level"])


    #######################################
    #         Brightness Control          #
    #######################################
    elif action == "brightness_up":
        brightness_up()
        update_history(function)

    elif action == "brightness_down":
        brightness_down()
        update_history(function)

    elif action == "set_brightness":
        set_brightness(function["parameters"]["level"])


    #######################################
    #           Window Control            #
    #######################################
    elif action == "focus_window":
        focus_window(function["target"])
        update_history(function)

    elif action == "minimize_window":
        minimize_window(function["target"])
        update_history(function)

    elif action == "maximize_window":
        maximize_window(function["target"])
        update_history(function)

    elif action == "snap_window":
        snap_window(function["target"], function["parameters"]["direction"])
        update_history(function)

    else:
        print("Unknown action")

