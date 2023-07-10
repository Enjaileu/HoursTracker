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

from monitor_utils.config.mhfx_path import file_template
import monitor_utils.config.monitor as monitor
from monitor_utils.mhfx_log import log

'''
def get_current_window():
    '
    Get the current active window and return it as a dict.

    :return: dict {'path':str, 'pid':int, 'title':str, 'name':str}
    '
    active_window = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(active_window)
    
    process = mhfx_psutil.Process(pid)
    try:
        file_path = process.exe()
    except mhfx_psutil.AccessDenied: 
        return {'path':None, 'pid':None, 'title':None, 'name': None}

    title = win32gui.GetWindowText(active_window)
    
    return {'path':file_path, 'pid':pid, 'title':title, 'name': process.name()}

'''


def get_current_window():
    '''
    Get the current active window and return it as a dict.

    :return: dict {'path':str, 'pid':int, 'title':str, 'name':str}
    '''
    try:
        active_window = win32gui.GetForegroundWindow()
        log(str(active_window))
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

def get_entity(filename):
    '''
    Convert a filename to a dict with info the monitor needs.

    :param filename: str or Path object
    :return: dict
    '''
    filename = str(filename).replace('\\', '/')
    data = {}
    try : 
        template_parts = re.findall(r'{(.*?)}', file_template)

        regex_pattern = file_template
        regex_pattern = regex_pattern.replace('{', r'(?P<').replace('}', r'>.*?)')


        matches = re.match(regex_pattern, str(filename))
        if matches:
            for template_part in template_parts:
                data[template_part] = matches.group(template_part)

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
        log("seems your file can't be convert to object, please verify you're in pipe")
"""
def does_process_exists(pid):
    '''
    Verify if the process still exists in windows.

    :param pid: str or int
    :return: bool
    '''
    try:
        pid = int(pid)
        exist = mhfx_psutil.pid_exists(pid)
        return exist
    except Exception as e:
        log(e)
"""

def does_process_exists(pid):
    '''
    Verify if the process still exists in windows.

    :param pid: str or int
    :return: bool
    '''
    try:
        pid = str(pid)
        tasklist_output = subprocess.check_output('tasklist', shell=True).decode(errors='ignore')
        return pid in tasklist_output
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

"""
def get_pid_by_process_name(process_names: list):
    '''
    Return the pid of a process by its name.
    If first try didn't succed, try again with a delay of 1 second.

    :param process_names: list of str
    :return: int or None
    '''
    pids = []
    for proc in mhfx_psutil.process_iter(['pid', 'name']):
        if proc.name() in process_names:
            pids.append(proc.pid)

        if pids == []:
            time.sleep(1)
            for proc in mhfx_psutil.process_iter(['pid', 'name']):
                if proc.name() in process_names:
                    pids.append(proc.pid)
    
    pid = pids[0] if pids else None

    if monitor.debug_mode:
        log(f"pids associated with this process : {pid}")
    return pid 
"""

def get_pid_by_process_name(process_names: list):
    '''
    Return the pid of a process by its name.
    If first try didn't succed, try again with a delay of 1 second.

    :param process_names: list of str
    :return: int or None
    '''
    def get_pids(process_names):
        pids = []
        try:
            tasklist_output = subprocess.check_output('tasklist', shell=True).decode(errors='ignore')
            log(str(tasklist_output))
            tasklist_lines = tasklist_output.split('\n')[3:]
            for line in tasklist_lines:
                if not line.strip():
                    continue
                parts = re.split(r'\s+', line)
                if parts[0] in process_names:
                    pids.append(int(parts[1]))
        except Exception as e:
            log(e)
        return pids

    pids = get_pids(process_names)
    if not pids:
        time.sleep(1)
        pids = get_pids(process_names)

    pid = pids[0] if pids else None

    if monitor.debug_mode:
        log(f"pids associated with this process : {pid}")
    return pid

def is_user_afk(afk_time: int):
    '''
    Checks whether the user has been AFK for longer than the time in seconds afk_time
    or if the computer is in standby mode.

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
    
    if elapsed_time <= afk_time:
        return win32gui.GetForegroundWindow() == 0 or win32gui.GetForegroundWindow() == win32gui.GetDesktopWindow()
    return False
    