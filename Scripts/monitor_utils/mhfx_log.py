'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''
import json
from datetime import datetime
from monitor_utils.config.mhfx_path import user_log

def log(error_message):
    '''
    Write error message to log file

    :param error_message: str or dict
    '''
    date = datetime.now().strftime('%d/%m/%y')
    time = datetime.now().strftime('%H:%M:%S')

    if isinstance(error_message, dict):
        error_message = json.dumps(error_message, indent=4)

    log_message = '\n' + date + ", " + time + " : " + error_message
    with open(user_log, 'a') as logfile:
        logfile.write(log_message)
