from assistant.tools import open_item, start_project, run_script, stop_project, list_processes, close_item
from assistant.alias_manager import create_alias, delete_alias, list_aliases, delete_all_aliases
from assistant.history import append_history, show_history, delete_history

from assistant.system_tools.volume import volume_up, volume_down, set_volume, mute, unmute
from assistant.system_tools.brightness import brightness_up, brightness_down, set_brightness
from assistant.system_tools.window import focus_window, minimize_window, maximize_window, snap_window, get_monitors_info, move_window_to_monitor
from assistant.system_tools.power import sleep_system, lock_system, restart_system, shutdown_system
from assistant.system_tools.clipboard import get_clipboard, set_clipboard, clear_clipboard

from assistant.brain.web_search_handler import classify_query

from assistant.external_connectors.news_handler import handle_news
from assistant.external_connectors.weather_handler import handle_weather


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
            append_history(function)

    elif action == "close":
        close = close_item(function["target"])

        if close:
            append_history(function)


    #######################################
    #           Aliases            #
    #######################################
    elif action == "create_alias":
        alias = function["target"]
        target = function["parameters"]["alias_for"]

        print(f"Alias: {alias}, Target: {target}")

        created = create_alias(alias, target)

        if created:
            append_history(function)

    elif action == 'delete_alias':
        deleted = delete_alias(function["target"])

        if deleted:
            append_history(function)

    elif action == 'delete_all_aliases':
        cleared = delete_all_aliases()

        if cleared:
            append_history(function)


    #######################################
    #         Proj/Script Control         #
    #######################################
    elif action == 'start_project':
        run = start_project(function["target"], function.get("parameters"))

        #Updating memory with project started
        if run:
            append_history(function)

    elif action == 'stop_project':
        stop = stop_project(function["target"], function.get("parameters"))

        #Updating memory with project stopped
        if stop:
            append_history(function)

    elif action == 'run_script':
        run = run_script(function["target"])

        #Updating memory with script executed
        if run:
            append_history(function)


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
        append_history(function)

    elif action == "volume_down":
        volume_down()
        append_history(function)

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
        append_history(function)

    elif action == "brightness_down":
        brightness_down()
        append_history(function)

    elif action == "set_brightness":
        set_brightness(function["parameters"]["level"])


    #######################################
    #           Window Control            #
    #######################################
    elif action == "focus_window":
        focus_window(function["target"])
        append_history(function)

    elif action == "minimize_window":
        minimize_window(function["target"])
        append_history(function)

    elif action == "maximize_window":
        maximize_window(function["target"])
        append_history(function)

    elif action == "snap_window":
        snap_window(function["target"], function["parameters"]["direction"])
        append_history(function)


    #######################################
    #           Power Control             #
    #######################################
    elif action in ["sleep_system", "lock_system", "restart_system", "shutdown_system"]:
        print(f"\n⚠️ Confirm power action: {action.replace('_', ' ')}")
        confirm = input("Type 'yes' to confirm: ").lower().strip()

        if confirm != "yes":
            print("Cancelled.")
            return

        append_history(function)

        if action == "sleep_system":
            sleep_system()
        elif action == "lock_system":
            lock_system()
        elif action == "restart_system":
            restart_system()
        elif action == "shutdown_system":
            shutdown_system()


    #######################################
    #           Power Control             #
    #######################################
    elif action == "get_clipboard":
        get_clipboard()

    elif action == "set_clipboard":
        set_clipboard(function["parameters"]["text"])

    elif action == "clear_clipboard":
        clear_clipboard()

    
    #######################################
    #          Monitor Control            #
    #######################################
    elif action == "list_monitors":
        get_monitors_info()

    elif action == "move_window_to_monitor":
        move_window_to_monitor(function["target"], function["parameters"]["monitor"])
        append_history(function)

    #######################################
    #             Web Search              #
    #######################################
    elif action == "search":
        parameters = function["parameters"] or {}
        routed = classify_query(parameters.get("query"))  # calls 120b
        print(f"Interpreted: {routed}")
        sub_action = routed["action"]
        sub_params = routed["parameters"]
        answer = ""

        if sub_action == "weather":
            answer = handle_weather(sub_params.get("location"))
        elif sub_action == "news":
            answer = handle_news(sub_params.get("topic"))
        else:  # general_search
            print("Nothing for now.")

        return answer


    else:
        print("Unknown action")