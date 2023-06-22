import json
import threading

from log import log
import data_management
from config.mhfx_path import user_last_json

def timer_finished():
    '''
    Reset last opened asset
    Write in last.json
    '''
    log('timer finished!')
    data_last ={
    "last_active_project": "",
    "last_opened": "",
    "last_department": "",
    "last_time": ""
    }
    
    json_obj = json.dumps(data_last, indent=4)
    data_management.write_to_file(json_obj, user_last_json)
        
def is_timer_running(t_timer):
    '''
    Return if the timer is running

    :return: bool
    '''
    return t_timer and t_timer.is_alive()

def run_timer(t_timer):
    '''
    Initialise new timer
    start timer
    '''
    log('timer run')
    t_timer = threading.Timer(120, timer_finished)
    t_timer.start()
    
def cancel_timer(t_timer):
    '''
    Cancel the timer
    Wait for it to finish task 
    '''
    log('timer cancel')
    if t_timer:
        t_timer.cancel()
        t_timer.join()

def reset_timer(t_timer):
    '''
    Reset the timer
    If it is already running, cancel it before
    Then run the timer 
    '''
    if is_timer_running(t_timer):
        cancel_timer(t_timer)
    run_timer(t_timer)