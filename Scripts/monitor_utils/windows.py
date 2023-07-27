'''
For Menhir FX
author: Angele Sionneau asionneau@artfx.fr
'''
import win32gui
import win32process
import win32api
import re
import time
import ctypes
import traceback
import win32com.client
import ast
from pathlib import Path

from monitor_utils.config.mhfx_path import file_template, file_template_bonus
import monitor_utils.config.monitor as monitor
from monitor_utils.mhfx_log import log

def get_current_window():
    '''
    Get the current active window and return it as a dict.

    :return: dict {'path':str, 'pid':int, 'title':str, 'name':str}
    '''
    try:
        active_window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(active_window)

        MAX_PATH = 260
        path_buffer = ctypes.create_unicode_buffer(MAX_PATH)
        h_process = ctypes.windll.kernel32.OpenProcess(1040, False, pid)

        if h_process:
            ctypes.windll.psapi.GetModuleFileNameExW(h_process, None, path_buffer, MAX_PATH)
            ctypes.windll.kernel32.CloseHandle(h_process)
            file_path = path_buffer.value
        else:
            return {'path': None, 'pid': None, 'title': None, 'name': None}

        title = win32gui.GetWindowText(active_window)
        name = file_path.split('\\')[-1]

        return {'path': file_path, 'pid': pid, 'title': title, 'name': name}
    except:
        log(traceback.format_exc())

def convert_file_to_data(filename, template):
    '''
    Function used by get_entity to convert a filename to a dict.
    
    :param filename: str or Path object
    '''
    data = {}
    try : 
        template_parts = re.findall(r'{(.*?)}', template)

        regex_pattern = template
        regex_pattern = regex_pattern.replace('{', r'(?P<').replace('}', r'>.*?)')

        matches = re.match(regex_pattern, str(filename))
        if matches:
            for template_part in template_parts:
                data[template_part] = matches.group(template_part)
        
        return data
    except Exception as e:
        log(traceback.format_exc())

def get_entity(filename):
    '''
    Convert a filename to a dict with info the monitor needs.

    :param filename: str or Path object
    :return: dict
    '''
    filename = str(filename).replace('\\', '/')
    try :
        data = convert_file_to_data(filename, file_template)

        try:
            data.get('asset_subtype').lower()
        except:
            if monitor.debug_mode:
                log("using bonus template")
            data = convert_file_to_data(filename, file_template_bonus)
            data['asset_subtype'] = data.get('asset_type')
            try:
                data.get('asset_subtype').lower()
            except:
                if monitor.debug_mode:
                    log("No template work for this asset")
                filename_path = Path(filename)
                data = {
                    'asset_type': 'unknown',
                    'asset_subtype': '',
                    'department': '',
                    'task': '',
                    'asset_name': str(filename_path.name),
                    'project_name': str(filename_path.stem)
                }

        entity ={
            'name': filename,
            'department': data.get('task'),
            'asset_type': data.get('asset_type').lower(),
            'project_name': data.get('project_name')
        }

        if "shot" in entity.get('asset_type'):
            entity['asset_name'] = f"{data.get('asset_subtype')} {data.get('asset_name')}"
        else:
            entity['asset_name'] = data.get('asset_name')
        
        return entity
    
    except:
        log(traceback.format_exc())
        log("seems your file can't be convert to object, please verify you're in pipe")


def does_process_exists(pid):
    '''
    Verify if the process still exists in windows and has an active window.

    :param pid: str or int
    :return: bool
    '''
    try:
        pid = int(pid)  # Make sure pid is an integer

        def callback(hwnd, hwnds):
            '''
            Callback function for win32gui.EnumWindows. It's called for each window handle and 
            adds the handle to the list if the associated process has the target pid.
            '''
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            if process_id == pid and win32gui.IsWindowVisible(hwnd):
                hwnds.append(hwnd)
            return True

        # Get all window handles associated with the target process
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)

        # If there's at least one window handle, the process is an application process
        if monitor.debug_mode:
            log(f"checking if process {pid} exists : {bool(hwnds)}")
        return bool(hwnds)
    except Exception as e:
        print(str(e))
        return False

def get_windows_username():
    '''
    This function retrieves the username of the currently logged-in user in Windows.

    Returns:
    username (str): The username of the currently logged-in user.
    '''
    try:
        username = win32api.GetUserName()
        return username
    except:
        return "Username unknown"

def get_pid_by_process_name(process_names: list, monitor_processes: dict):
    '''
    Somehow thanks to the process names, get the pid of the new process opened.

    :param process_names: list
    :param monitor_processes: dict

    :return: pid of the process (int) or None if not found.
    '''
    # remove the process from the list if not right monitor neither right executable
    try:
        monitor_processes_copy = monitor_processes.copy()
        for pid, infos in monitor_processes_copy.items():
            if process_names[0] not in ast.literal_eval(infos.get('executable')) or not does_process_exists(pid):
                monitor_processes.pop(pid)

        found = False
        incr = 0
        timeout = monitor.wait_sec
        pids = []

        while found == False and incr < timeout:
            try:
                wmi = win32com.client.GetObject("winmgmts:")
                processes = wmi.InstancesOf("Win32_Process")
                for process in processes:
                    proc_name = process.Properties_("Name").Value
                    if proc_name in process_names:
                        pids.append(process.Properties_("ProcessId").Value)
            except Exception as e:
                log(traceback.format_exc())

            if len(pids) > len(monitor_processes) and len(pids) > 0:
                found = True
            else:
                time.sleep(1)
                incr += 1
        if len(pids) > len(monitor_processes):
            keys = monitor_processes.keys()
            keys_int = [int(num) for num in keys]
            diff = set(pids) - set(keys_int)
            return list(diff)[0]
        
        if monitor.debug_mode:
            log(f"No pid associated with this process.")
        return None
    except:
        log(traceback.format_exc())

def is_user_afk(afk_time: int):
    '''
    This function checks if the user has been inactive for a specified amount of time.

    Parameters:
    afk_time (int): The maximum allowed time of user inactivity in seconds.
 
    Returns:
    is_afk (bool): True if the user is inactive, False otherwise.
    '''
    try:
        # Get when the last input event happened
        last_input_time = win32api.GetLastInputInfo()

        # Get the current time
        current_time = win32api.GetTickCount()

        # Calculate the elapsed time
        elapsed_time = (current_time - last_input_time) / 1000
        if monitor.debug_mode:
            log(f"Last user input happened {elapsed_time} seconds ago. max allowed = {afk_time}")
        
        return elapsed_time >= afk_time
    except:
        log(traceback.format_exc())