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
    

