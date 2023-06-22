'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''

import traceback
from mhfx_log import log

def initialise_data(date, entity, start_time):
    '''
    Initialise complete data template of tracking hours

    :param date: date of the day
    :param entity: entity of the asset opened
    :param start_time: time when the asset was opened
    :return: dict 
    '''
    try:
        return {"days":[ initialise_day(date, entity, start_time)]}
    except Exception as e:
        log(traceback.format_exc())

def initialise_day(date, entity, start_time):
    '''
    Initialise a new day to append to the data

    :param date: date of the day
    :param entity: entity of the asset opened
    :param start_time: time when the asset was opened
    :return: dict 
    '''
    try : 
        return {"date": date, "projects": [initialise_project(entity, start_time)]}
    except Exception as e:
        log(traceback.format_exc())

def initialise_project(entity, start_time):
    '''
    Initialise a new project to append to the date in the data

    :param entity: entity of the asset opened
    :param start_time: time when the asset was opened
    :return: dict
    '''
    try:
        project = {
            'project_name': entity.get('project_name'),
            'project_sessions':[initialise_project_sessions(entity, start_time)]
        }
        return project
    except Exception as e:
        log(traceback.format_exc())
    
def initialise_project_sessions(entity, start_time):
    '''
    Initialise a new project session

    :param entity: entity of the asset opened
    :param start_time: time when the asset was opened
    :return: dict
    '''
    try:
        sessions = {
            'asset_name': entity.get('asset_name'),
            'department': entity.get('department'),
            'asset_sessions': [initialise_asset_session(start_time)],
            'total_time': '0:00:00'
        }
        return sessions
    except Exception as e:
        log(traceback.format_exc())

def initialise_asset_session(start_time):
    '''
    Initialise a new asset session

    :param start_time: time when the asset was opened
    :return: dict
    '''
    try:
        session = {
            'start_time': start_time,
            'last_action_time': start_time,
            'total_time': '0:00:00'
        }
        return session
    except Exception as e:
        log(traceback.format_exc())

