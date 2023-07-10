'''
For Menhir FX

Get the user config store in config.ini

author: Angele Sionneau - asionneau@artfx.fr
'''

import configparser
from monitor_utils.config.mhfx_path import user_config

config = configparser.ConfigParser()

try:
    config.read(user_config)

    # Monitor
    wait_sec = config.getint('Monitor', 'monitor_interval_seconds')
    total_cycle = config.getint('Monitor', 'data_save_interval_seconds')

    # AFK
    max_afk_cycle  = config.getint('AFK', 'session_afk_seconds')
    user_afk_sec  = config.getint('AFK', 'user_afk_seconds')
    wait_sec_afk  = config.getint('AFK', 'monitor_interval_afk_seconds')

    # Debug
    debug_mode = config.getboolean('Debug', 'debug_mode')

except:
    wait_sec = 30 # how many second between 2 check the window in foreground
    total_cycle = 60 * 5 # how many second before write data
    max_afk_cycle = 60 * 30 # How many seconds before we consider the session is afk/old
    user_afk_sec = 60 * 45 # How many seconds before we consider the user is afk
    wait_sec_afk = 60 * 5 # how many second between 2 check the window in foreground when user is afk

    debug_mode = False