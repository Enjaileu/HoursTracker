import sys
sys.path.append('R:/Python/tiers')

import win32gui
import win32process
import psutil
import win32api
import re

from utils.config.mhfx_path import file_template
from utils.mhfx_log import log

def get_current_window():
    active_window = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(active_window)
    
    process = psutil.Process(pid)
    try:
        file_path = process.exe()
    except psutil.AccessDenied: 
        return {'path':None, 'pid':None, 'title':None, 'name': None}

    title = win32gui.GetWindowText(active_window)
    
    return {'path':file_path, 'pid':pid, 'title':title, 'name': process.name()}

def get_entity(filename):
    filename = str(filename.as_posix())
    data = {}
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
    
    log(f"get_entity, result entity = {entity}")

    return entity

def does_process_exists(pid):
    return psutil.pid_exists(pid)


def get_windows_username():
    username = win32api.GetUserName()
    return username

def get_pid_by_process_name(process_name):
    pids = []

    for proc in psutil.process_iter(['pid', 'name']):
        if proc.name() in process_name:
            pids.append(proc.pid)
    pid = pids[-1] if pids else None
    log(f"pid found = {pid}")
    return pid 