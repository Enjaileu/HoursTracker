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
import subprocess

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
    Verify if the process still exists in windows.

    :param pid: str or int
    :return: bool
    '''
    try:
        pid = str(pid)
        tasklist_output = subprocess.check_output('tasklist', shell=True).decode(errors='ignore')
        tasklist_lines = tasklist_output.split('\n')[3:]
        for line in tasklist_lines:
            if not line.strip():
                continue
            task_pid = line[27:34].strip()  # Extract the PID based on its fixed position
            if pid == task_pid:
                return True
        return False
    except Exception as e:
        log(str(e))
        return False


def get_windows_username():
    '''
    Get the windows session username.
    
    :return: str
    '''
    username = win32api.GetUserName()
    return username


def get_pid_by_process_name(process_names: list):
    '''
    Return the pid of a process by its name.
    If first try didn't succed, try again with a delay of 1 second.

    :param process_names: list of str
    :return: int or None
    '''
    found = False
    incr = 0
    timeout = monitor.wait_sec
    pids = []

    while found == False and incr < timeout:
        try:
            tasklist_output = subprocess.check_output('tasklist', shell=True).decode(errors='ignore')
            tasklist_lines = tasklist_output.split('\n')[3:]
            for line in tasklist_lines:
                if not line.strip():
                    continue
                proc_name = line[:27].strip()
                pid = line[27:34].strip()
                if proc_name in process_names and pid:
                    pids.append(int(pid))
        except Exception as e:
            log(e)

        if len(pids) > 0:
            found = True
        else:
            time.sleep(1)
            incr += 1

            if monitor.debug_mode:
                log(f"pid not found")

    pid = pids[0] if pids else None

    if monitor.debug_mode:
        log(f"pids associated with this process : {pid}")
    return pid

def is_user_afk(afk_time: int):
    '''
    Checks whether the user has been AFK for longer than the time in seconds afk_time.

    :param afk_time: int
    :return: bool
    '''
    # Get when the last input event happened
    last_input_time = win32api.GetLastInputInfo()

    # Get the current time
    current_time = win32api.GetTickCount()

    # Calculate the elapsed time
    elapsed_time = (current_time - last_input_time) / 1000
    if monitor.debug_mode:
        log(f"Last user input happened {elapsed_time} seconds ago.")
        log(f"max allowed = {afk_time}")
    
    return elapsed_time >= afk_time
    