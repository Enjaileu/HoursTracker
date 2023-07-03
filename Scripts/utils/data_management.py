'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''
from enum import Enum
import traceback
from mhfx_log import log
from datetime import datetime, timedelta
import date as dt
from windows import get_windows_username
import data_initialise as di

## MODIFY

class Missing(Enum):
    ALL = 0
    DAY = 1
    PROJECT = 2
    ENTITY = 3
    SESSION = 4
    NOTHING = 5


def add_project(data, project):
    '''
    Append a project in the data in the last day

    :param data: dict
    :param project: dict
    :return: dict, data modified
    '''
    data.get('days')[-1].get('projects').append(project)
    log(f"data dans add_project = {data}")
    return data

def add_project_session(data, session, entity):
    '''
    Append a project session in the data in the right project

    :param data: dict
    :param session: dict
    :return: dict, data modified
    '''
    projects = data.get('days')[-1].get('projects')
    for p in projects:
        if p.get('project_name') == entity.get('project_name'):
            p.get('project_sessions').append(session)

    return data
    
def add_asset_session(data, entity, session):
    '''
    Append an asset session in the data in the right project session

    :param data: dict
    :param entity: dict
    :param session: dict
    :return: dict, data modified
    '''
    projects = data.get('days')[-1].get('projects')
    for p in projects:
        if p.get('project_name') == entity.get('project_name'):
            project_sessions = p.get('project_sessions')
            for ps in project_sessions:
                if ps.get('asset_name') == entity.get('asset_name') and ps.get('department') == entity.get('department'):
                    ps.get('asset_sessions').append(session)

    return data

## CHECK

def does_day_exist(data, date):
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
    
def initialise_data(data, entity, date, first):
    log('initialise_data()')
    if data == {}:
        return di.initialise_data(date, entity, first)

    if not does_day_exist(data, date):
        new_day = di.initialise_day(date, entity, first)
        data.get('days').append(new_day)
        return data
    
    projects = data.get('days')[-1].get('projects')
    for p in projects:
        log(f"comparaison {p.get('project_name')} = {entity.get('project_name')}")
        if p.get('project_name') == entity.get('project_name'):
            sessions = p.get('project_sessions')
            for s in sessions:
                log(f"comparaison {s.get('asset_name')} = {entity.get('asset_name')} AND  {s.get('department') } = {entity.get('department')}")
                log(f" result = {s.get('asset_name') == entity.get('asset_name')} / {s.get('department') == entity.get('department')}")
                if s.get('asset_name') == entity.get('asset_name') and s.get('department') == entity.get('department'):
                    try:
                        log(f"project_session  = {s}")
                        last_session = s.get('asset_sessions')[-1]
                        log(f"last session = {last_session}")
                        log(f"start_time = {last_session.get('start_time')}")
                        session_first = last_session.get('start_time')
                        log(f"{first}")
                        if session_first == first:
                            # no change
                            log('session already exists so no change in data')
                            return data
                        else:
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


def update_data(data, entity, time, first):
    log("dm.update_data")
    log(f"want to update with this : {entity.get('asset_name')} - {time} - {first}")
    now = datetime.now()
    date = now.strftime('%d/%m/%y')
    
    data = create_data(data, entity, first.strftime('%H:%M:%S'))

    try:
        # update session
        days = data.get('days')

        for d in days:
            if d.get('date') ==  date:
                project = entity.get('project_name')
                projects = d.get('projects')
                for p in projects:
                    if p.get('project_name') == project:
                        project_sessions = p.get('project_sessions')
                        for ps in project_sessions:
                            total_time = timedelta(seconds=0)

                            asset_name = ps.get('asset_name')
                            department = ps.get('department')
                            if asset_name == entity.get('asset_name') and department == entity.get('department'):
                                sessions = ps.get('asset_sessions')
                                log(f"sessions list = {sessions}")

                                log(f"update last session")
                                # update last action time
                                sessions[-1]['last_action_time'] = now.strftime('%H:%M:%S')
                                # update total_time session
                                hours = time // 3600
                                minutes = (time % 3600) // 60
                                seconds = time % 60
                                sessions[-1]['total_time'] = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
                                log(f"session updated : {sessions[-1]}")
                            
                                # update total_time project session
                                for s in sessions:
                                    tt = dt.get_time_as_datetime_obj(s.get('total_time'))
                                    delta_tt = timedelta(hours=tt.hour, minutes=tt.minute, seconds=tt.second)
                                    total_time += delta_tt
                                ps['total_time'] = str(total_time)
                                break
                        break
    
        return data 

    except Exception as e:
        log(traceback.format_exc())

def create_data(data, entity, first):
        log("dm.create_data()")
        try:
            # Get scene open action relevant data
            user = get_windows_username()
            now = datetime.now()
            date = now.strftime('%d/%m/%y')
            year = now.isocalendar()[0]
            week = now.isocalendar()[1]
            week_description = dt.get_week_definition()

            data = initialise_data(data, entity, date, first)

            # Set last datas
            data['user_id'] = user
            data['year'] = str(year)
            data['week'] = str(week)
            data['week_description'] = week_description

            return data
            
        except Exception as e:
            log(traceback.format_exc())