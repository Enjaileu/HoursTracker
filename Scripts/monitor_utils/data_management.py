'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''
import traceback
import json
from datetime import datetime, timedelta

import monitor_utils.date as dt
from monitor_utils.windows import get_windows_username, does_process_exists
import monitor_utils.data_initialise as di
import monitor_utils.file as file
import monitor_utils.config.mhfx_path as mhfx_path
from monitor_utils.mhfx_log import log
import monitor_utils.config.monitor as monitor

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
                                        if monitor.debug_mode:
                                            log(f"Update tracker data: {date} : {project} : {asset_name}-{department} : {s}")
                                    
                                    # update total_time project session
                                    tt = dt.get_time_as_datetime_obj(s.get('total_time'))
                                    delta_tt = timedelta(hours=tt.hour, minutes=tt.minute, seconds=tt.second)
                                    total_time += delta_tt
                                ps['total_time'] = str(total_time)
                                if monitor.debug_mode:
                                    log(f"Total time updated : {asset_name}-{department} : {ps['total_time']}")
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
    try:
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
    except:
        log(traceback.format_exc())

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
    try:
        content = "var data = '{}'".format(js_obj)
        file.write_to_file(content, mhfx_path.user_data_js)
        
        file.write_to_file(json_obj, mhfx_path.user_data_json)
    except:
        log(traceback.format_exc())

def push_processes(content, monitor_id=-1):
    '''
    Write list of processes to user's tmp folder.

    :param content: dict
    :param monitor_id: int
    '''
    try:
        data = file.get_data(mhfx_path.user_tmp_processes)
        data_copy = data.copy()
        for pid, infos in data_copy.items():
            if infos.get('monitor_id') == str(monitor_id) or monitor_id == -1:
                if not does_process_exists(pid):
                    data.pop(str(pid))
        data.update(content)
        json_obj = json.dumps(data, indent=4)
        file.write_to_file(json_obj, mhfx_path.user_tmp_processes)
    except:
        log(traceback.format_exc())

def remove_processes(pids : list):
    '''
    Remove processes from tmp file processes.json with the pid in pids.

    :param pids : list of int or list of str of int
    '''
    try:
        data = file.get_data(mhfx_path.user_tmp_processes)
        for pid in pids:
            data.pop(str(pid))
        json_obj = json.dumps(data, indent=4)
        file.write_to_file(json_obj, mhfx_path.user_tmp_processes)
    except:
        log(traceback.format_exc())

def get_processes(monitor_id=-1):
    '''
    Get the dictionnary of processes written in the user's tmp folder.
    If monitor_id is -1, return all processes.
    Else return only the process monitored by the given monitor_id.
    
    :return: dict
    '''
    try:
        data =  file.get_data(mhfx_path.user_tmp_processes)

        if monitor_id == -1:
            return data
        else:
            m_id = str(monitor_id)
            data_to_return = {}

            if data != {}:
                for pid, infos in data.items():
                    if infos.get('monitor_id') == m_id:
                        data_to_return[pid] = infos

            return data_to_return
    except:
        log(traceback.format_exc())

def get_last_process(monitor_id=-1):
    '''
    Return data in tmp file last_process.
    If monitor_id specified, return last_process only if it is monitored by the given monitor_id.
    
    :param monitor_id: int 
    '''
    try:
        last = file.get_data(mhfx_path.user_tmp_last_proc)
        m_id = str(monitor_id)
        if last != {}:
            pid = next(iter(last))
            if m_id == last[pid].get('monitor_id') or m_id == "-1":
                return last
        return None
    except:
        log(traceback.format_exc())

def push_last_process(last):
    '''
    Write dict in param last to tmp file last_process.json.

    :param last: dict
    '''
    try:
        json_obj = json.dumps(last, indent=4)
        file.write_to_file(json_obj, mhfx_path.user_tmp_last_proc)
    except:
        log(traceback.format_exc())