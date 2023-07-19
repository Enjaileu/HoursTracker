'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''
import traceback
import json
from datetime import datetime, timedelta

import monitor_utils.date as dt
from monitor_utils.windows import get_windows_username
import monitor_utils.data_initialise as di
import monitor_utils.file as file
import monitor_utils.config.mhfx_path as mhfx_path
from monitor_utils.mhfx_log import log

## MODIFY
def add_project(data: dict, project: dict):
    '''
    Append a project in the data in the last day

    :param data: dict
    :param project: dict
    :return: dict, data modified
    '''
    try:
        data.get('days')[-1].get('projects').append(project)
        return data
    except:
        log.error(traceback.format_exc())

def add_project_session(data: dict, session: dict, entity: dict):
    '''
    Append a project session in the data in the right project

    :param data: dict
    :param session: dict
    :return: dict, data modified
    '''
    try:
        projects = data.get('days')[-1].get('projects')
        for p in projects:
            if p.get('project_name') == entity.get('project_name'):
                p.get('project_sessions').append(session)

        return data
    except:
        log.error(traceback.format_exc())
 
def add_asset_session(data: dict, entity: dict, session: dict):
    '''
    Append an asset session in the data in the right project session

    :param data: dict
    :param entity: dict
    :param session: dict
    :return: dict, data modified
    '''
    try:
        projects = data.get('days')[-1].get('projects')
        for p in projects:
            if p.get('project_name') == entity.get('project_name'):
                project_sessions = p.get('project_sessions')
                for ps in project_sessions:
                    if ps.get('asset_name') == entity.get('asset_name') and ps.get('department') == entity.get('department'):
                        ps.get('asset_sessions').append(session)

        return data
    except:
        log.error(traceback.format_exc())


def update_data(data: dict, entity: dict, time: int, first: str):
    '''
    Update tracker data with entity.

    :param data: dict, tracker data
    :param entity: dict, session info
    :param time: int, how many seconds the session was used
    :param first: string, the time %H%M%S the session was opened
    :return: dict, data modified
    '''

    # get current time
    now = datetime.now()
    date = now.strftime('%d/%m/%y')
    data = create_data(data, entity, first)
    try:
        # update session
        days = data.get('days')

        for d in days:
            if d.get('date') ==  date:
                project = entity.get('project_name')
                for p in d.get('projects'):
                    if p.get('project_name') == project:
                        for ps in p.get('project_sessions'):
                            total_time = timedelta(seconds=0)
                            asset_name = ps.get('asset_name')
                            department = ps.get('department')
                            if asset_name == entity.get('asset_name') and department == entity.get('department'):
                                for s in reversed(ps.get('asset_sessions')):
                                    if s.get('start_time') == first:
                                        # update last action time
                                        s['last_action_time'] = now.strftime('%H:%M:%S')
                                        # update total_time session
                                        hours = time // 3600
                                        minutes = (time % 3600) // 60
                                        seconds = time % 60
                                        s['total_time'] = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
                                    
                                    # update total_time project session
                                    tt = dt.get_time_as_datetime_obj(s.get('total_time'))
                                    delta_tt = timedelta(hours=tt.hour, minutes=tt.minute, seconds=tt.second)
                                    total_time += delta_tt
                                ps['total_time'] = str(total_time)
                                break
                        break
        return data 

    except Exception as e:
        log(traceback.format_exc())

def create_data(data: dict, entity: dict, first: str):
    '''
    Prepare a clean version of the tracker data with the entity session info.
    
    :param data: dict, tracker data
    :param entity: dict, session info
    :param first: string, the time %H%M%S the session was opened
    :return: dict, data modified
    '''
    try:
        # Get scene open action relevant data
        user = get_windows_username()
        now = datetime.now()
        date = now.strftime('%d/%m/%y')
        year = now.isocalendar()[0]
        week = now.isocalendar()[1]
        week_description = dt.get_week_definition()

        # push entity session in tracker data
        data = initialise_data(data, entity, date, first)

        # Set last datas
        data['user_id'] = user
        data['year'] = str(year)
        data['week'] = str(week)
        data['week_description'] = week_description

        return data
        
    except Exception as e:
        log(traceback.format_exc())

def initialise_data(data: dict, entity: dict, date: str, first: str):
    '''
    Depending on the entity, will create its data in the right place in the tracker data.

    :param data: dict, tracker data
    :param entity: dict, session entity
    :param date: string, current date
    :param first: string, when the session was opened
    :return: dict, tracker data modified
    '''

    # if no data, initialise complete data set with entity
    if data == {}:
        return di.initialise_data(date, entity, first)

    # if current date don't exist in tracker data, create it with entity
    if not does_day_exist(data, date):
        new_day = di.initialise_day(date, entity, first)
        data.get('days').append(new_day)
        return data
    
    # others situations
    projects = data.get('days')[-1].get('projects')
    for p in projects:
        if p.get('project_name') == entity.get('project_name'):
            sessions = p.get('project_sessions')
            for s in sessions:
                if s.get('asset_name') == entity.get('asset_name') and s.get('department') == entity.get('department'):
                    try:
                        asset_sessions = s.get('asset_sessions')
                        for a_s in reversed(asset_sessions):
                            # asset session already exists
                            if a_s.get('start_time') == first:
                                return data

                        # need new asset session
                        session = di.initialise_asset_session(first)
                        return add_asset_session(data, entity, session)
                    except:
                        # need new asset session
                        session = di.initialise_asset_session(first)
                        return add_asset_session(data, entity, session)
            # entity not found in project sessions
            session = di.initialise_project_sessions(entity, first)
            return add_project_session(data, session, entity)
    # project was not found
    project = di.initialise_project(entity, first)
    return add_project(data, project)

## CHECK

def does_day_exist(data: dict, date: str):
    '''
    Checks if the given date exists in the data

    :param data: dict
    :param date: string
    :return: bool
    '''
    try:
        for d in data.get('days'):
            if d.get('date') == date:
                return True
    except Exception as e:
        log(traceback.format_exc())

# WRITE

def push_data(js_obj, json_obj):
    '''
    Write tracker data to files.

    :param js_obj: json dict, tracker data
    :param json_obj: json dict, tracker data
    '''
    content = "var data = '{}'".format(js_obj)
    file.write_to_file(content, mhfx_path.user_data_js)
    
    file.write_to_file(json_obj, mhfx_path.user_data_json)

def push_processes(content):
    '''
    Write list of processes to user's tmp folder.
    '''
    json_obj = json.dumps(content, indent=4)
    file.write_to_file(json_obj, mhfx_path.user_tmp_processes)

def get_processes():
    '''
    Get the dictionnary of processes written in the user's tmp folder.
    
    :return: dict
    '''
    return file.get_data(mhfx_path.user_tmp_processes)