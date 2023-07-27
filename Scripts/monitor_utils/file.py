'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''
import os
import traceback
import json
import shutil

from monitor_utils.mhfx_log import log
from monitor_utils.config import mhfx_path

def get_data(path):
    '''
    Read json data from a given path and return its data

    :param path: string
    :return: dict
    '''
    path = str(path)
    try:
        # Open user json data and laod it to data
        with open(path, 'r') as json_file:
            try:
                raw_data = json_file.read()
            except Exception as e:
                log(traceback.format_exc())
                log(str(e))
            data = json.loads(raw_data)
        
        if data == None:
            data = {} 
    except:
        log(traceback.format_exc())
        # If json file empty return empty dict/json object
        data = {}
    
    return data

def write_to_file(content, filename):
    '''
    Writes given content to the given filename.

    :param content: dict
    :param filename: string
    '''
    try:
        output_file = open(filename, 'w')
        output_file.write(content)
        output_file.close()
    except:
        log(traceback.format_exc())

def backup_data(data):
    """
    Copies the user's json data to a backup location
    Fill json backups with new backup location

    :param data: dict, data to backup
    """
    try:
        # last week and last year
        week = data.get('week')
        year = data.get('year')
        week_definition = data.get('week_description')

        # write hours data
        src = mhfx_path.user_data_json
        dst = f"{mhfx_path.user_data_backup}{week}_{year}_hours.json"
        shutil.copy(src, dst)

        src = mhfx_path.user_data_js
        dst = f"{mhfx_path.user_data_backup}{week}_{year}_hours.js"
        shutil.copy(src, dst)

        src = mhfx_path.user_log
        dst = f"{mhfx_path.user_data_backup}{week}_{year}_log.txt"
        shutil.copy(src, dst)

        # write backup data
        new_bckp = create_backup_info(week, year, week_definition)
        bckp_info = get_data(mhfx_path.user_list_backup_json)
        if bckp_info == {}:
            bckp_info = {"backups":[]}
        bckp_info.get('backups').insert(0, new_bckp)

        js_obj = json.dumps(bckp_info)
        content = f"var data = '{js_obj}'"
        write_to_file(content, mhfx_path.user_list_backup_js)

        json_obj = json.dumps(bckp_info, indent=4)
        write_to_file(json_obj, mhfx_path.user_list_backup_json)

        write_to_file('', mhfx_path.user_log)
    except:
        log(traceback.format_exc())

def reset_user_data():
    """
    Resets the json, js, and txt files containing the user's data
    """
    try:
        file_paths = [mhfx_path.user_data_json, mhfx_path.user_data_js, mhfx_path.user_log, mhfx_path.user_tmp_processes, mhfx_path.user_tmp_last_proc]

        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
            with open(file_path, 'w') as file:
                if file_path.endswith('.json'):
                    file.write("{}")
                else:
                    file.write('')
    except:
        log(traceback.format_exc())

def create_backup_info(week, year, week_definition):
    '''
    Creates a backup info dict and return it

    :param week: int
    :param year: int
    :return: dict
    '''
    try:
        bkp = {
            "week": str(week),
            "year": str(year),
            "path": f"{mhfx_path.user_data_backup}{week}_{year}_hours.js",
            "week_description": str(week_definition)
        }

        return bkp
    except:
        log(traceback.format_exc())