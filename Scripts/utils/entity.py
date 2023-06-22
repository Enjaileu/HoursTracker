'''
authors:
Elise Vidal - evidal@artfx.fr
Angele Sionneau - asionneau@artfx.fr
'''

import os
import traceback

import mhfx_log
from mhfx_log import log

def get_current_project(core):
    '''
    Returns the project's name

    :return: string
    '''
    try:
        project_name = core.projectName
    except:
        project_path = core.getConfig("globals", "current project")
        project_name = os.path.basename(os.path.dirname(os.path.dirname(project_path)))

    return project_name
  

def get_username(core):
    '''
    Returns the user's name

    :return: string
    '''
    try:
        log(f"user try = {core.getConfig('globals', 'username')}")
        return core.getConfig("globals", "username")
    except:
        log(f"user except = {core.username}")
        return core.username

def get_entity(core):
        '''
        Get current file info and convert it to entity

        :return: dict
        '''
        try :
            file_name = core.getCurrentFileName()
            log(f"file_name = {file_name}")
            data = core.getScenefileData(file_name)
            log(f"scene file data = {data}")
            if data == {}:
                return {}
            else:
                entity = {
                    'name': data.get('filename'),
                    'department': data.get('task'),
                    'asset_type': data.get('type'),
                    'project_name': get_current_project(core)
                }

                if entity.get('asset_type') == 'shot':
                    entity['asset_name'] = f"{data.get('sequence')}{data.get('shot')}"
                else:
                    entity['asset_name'] = data.get('asset')

                return entity
        except Exception as e:
            mhfx_log.log(traceback.format_exc())
            return {}

## CHECK
            
def is_same_asset(current, last):
    '''
    Return if the asset store in last.json is the same as the entity

    :param entity: dict
    :return: bool
    '''
    try:
        return last['last_active_project'] == current.get('project_name') and last['last_opened'] == current.get('asset_name') and last["last_department"] == current.get('department')
    except Exception as e:
        mhfx_log.log(traceback.format_exc())
        return False
    
def does_project_exist(data, core):
    '''
    Checks if the given project exists in the data

    :param data: dict
    :return: bool
    '''
    try:
        project = get_current_project(core)
        projects = data.get('days')[-1].get('projects')
        for p in projects:
            if p.get('project_name') == project:
                return True

    except Exception as e:
        mhfx_log.log(traceback.format_exc())

def is_project_session_exist(data, entity, core):
    '''
    Checks if the given project session exists in the data

    :param data: dict
    :param entity: dict
    :return: bool
    '''
    projects = data.get('days')[-1].get('projects')
    for p in projects:
        if p.get('project_name') == get_current_project(core):
            sessions = p.get('project_sessions')
            for s in sessions:
                if s.get('asset_name') == entity.get('asset_name') and s.get('department') == entity.get('department'):
                    return True
    
    return False