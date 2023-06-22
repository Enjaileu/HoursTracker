'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''
import traceback
from mhfx_log import log

## MODIFY

def update_last(data_last, entity):
    '''
    Updates the last active project and last opened asset in the data

    :param data_last: dict
    :param entity: dict
    :return: dict, data modified
    '''
    data_last['last_active_project'] = entity.get('project_name')
    data_last['last_opened'] = entity.get('asset_name')
    data_last['last_department'] = entity.get('department')
    data_last['last_time'] = datetime.now().strftime('%H:%M:%S')

    return data_last

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