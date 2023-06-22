'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''

from datetime import datetime
from config.mhfx_path import user_log

def log(error_message):
        date = datetime.now().strftime('%d/%m/%y')
        time = datetime.now().strftime('%H:%M:%S')
        log_message = '\n' + date + ", " + time + " : " + error_message
        with open(user_log, 'a') as logfile:
            logfile.write(log_message)


if __name__ == "__main__":
    print(f"user_log = {user_log}")
    print(user_log)