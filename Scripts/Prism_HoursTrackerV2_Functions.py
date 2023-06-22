# Author: Elise Vidal
# Contact :  evidal@artfx.fr

# Author: Angèle Sionneau
# Contact :  asionneau@artfx.fr

import os
import json
import shutil
import traceback
from datetime import datetime, timedelta
from pathlib import Path

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

from utils.config import mhfx_path, mhfx_disk
import utils.entity as ntt
from utils.mhfx_log import log
import utils.date as dt
import utils.data_management as dm
import utils.data_initialise as di
import utils.file as file


class Prism_HoursTrackerV2_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.version = self.core.version.split('.', 3)[-1]

        # Register callback functions
        self.core.callbacks.registerCallback(
            "onSceneOpen", self.onSceneOpen, plugin=self)
        self.core.callbacks.registerCallback(
            "sceneSaved", lambda *args: self.update_callback(cll_name="sceneSaved", *args), plugin=self)
        self.core.callbacks.registerCallback(
            "onStateManagerShow", lambda *args: self.update_callback(cll_name="onStateManagerShow", *args), plugin=self)
        self.core.callbacks.registerCallback(
            "onPublish", lambda *args: self.update_callback(cll_name="onPublish", *args), plugin=self)
        self.core.callbacks.registerCallback(
            "postPublish", lambda *args: self.update_callback(cll_name="postPublish", *args), plugin=self)
        self.core.callbacks.registerCallback(
            "postExport", lambda *args: self.update_callback(cll_name="postExport", *args), plugin=self)

        if not os.path.exists(mhfx_path.user_data_dir):
            os.makedirs(mhfx_path.user_data_dir)
        
        if not os.path.exists(mhfx_path.user_log):
            open(mhfx_path.user_log, 'a').close()

        if not os.path.exists(mhfx_path.user_data_dir):
            os.makedirs(mhfx_path.user_data_dir)

        if not os.path.exists(mhfx_path.user_data_backup):
            os.makedirs(mhfx_path.user_data_backup)

        if not os.path.exists(mhfx_path.user_list_backup_json):
            with open(mhfx_path.user_list_backup_json, 'a') as json_file:
                json_file.write('{}')

        if not os.path.exists(mhfx_path.user_list_backup_js):
            open(mhfx_path.user_list_backup_js, 'a').close()

        if not os.path.exists(mhfx_path.user_data_json):
            with open(mhfx_path.user_data_json, 'a') as json_file:
                json_file.write('{}')

        if not os.path.exists(mhfx_path.user_last_json):
            with open(mhfx_path.user_last_json, 'a') as json_file:
                json_file.write('{}')

        if not os.path.exists(mhfx_path.user_data_js):
            open(mhfx_path.user_data_js, 'a').close()
        
        if not os.path.exists(mhfx_path.user_data_html):
            src = f'R:/Prism/Plugins/{self.version}/HoursTracker/Scripts/templates/hours.html'
            dst = mhfx_path.user_data_html
            shutil.copy(src, dst)

        if not os.path.exists(mhfx_path.user_data_css):
            src = f'R:/Prism/Plugins/{self.version}/HoursTracker/Scripts/templates/style.css'
            dst = mhfx_path.user_data_css
            shutil.copy(src, dst)

        # create thread dedicated to timer
        self.t_timer = None

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

# UTILITY FUNCTIONS
    def is_disk_allowed(self, path):
        '''
        return if the is on a disk allowed by the plugin

        :param path: path of the file
        :return: bool
        '''
        letter = Path(path).parts[0]
        log(f"letter = {letter}")
        return letter not in mhfx_disk.not_allowed


# LOGIC
    def create_data(self, entity={}):
        """
        Initialise data that goes in hours.json and hours.js
        Write all the data in the files

        :param entity: dict
        """
        if 'noUI' not in self.core.prismArgs:
            try:
                # Get scene open action relevant data
                user = ntt.get_username(self.core)
                now = datetime.now()
                date = now.strftime('%d/%m/%y')
                start_time = now.strftime('%H:%M:%S')
                year = now.isocalendar()[0]
                week = now.isocalendar()[1]
                week_description = dt.get_week_definition()

                # Get data from file
                try:
                    # Open user json data and laod it to data
                    data = file.get_data(mhfx_path.user_data_json)
                except:
                    # If json file empty return empty dict/json object
                    data = {}
                
                # Get data_last from file
                try:
                    data_last = file.get_data(mhfx_path.user_last_json)
                except:
                    data_last = {}

                # If data is empty initialise it
                if data == {}:
                    data = di.initialise_data(date, entity, start_time)
                
                # Check if it's a new week, archive and reset data if it is
                elif dt.is_new_week(data, week) is True:
                    file.backup_data(data)
                    file.reset_user_data()
                    data = di.initialise_data(date, entity, start_time)
                
                # Check if current day exists and create data if necessary
                elif not dm.does_day_exist(data, date):
                    new_day = di.initialise_day(date, entity, start_time)
                    data.get('days').append(new_day)
                    
                # Does the current project exist for today date, if not initialise it
                elif not ntt.does_project_exist(data, self.core):
                    project = di.initialise_project(entity, start_time)
                    log(f"avant add_project, data = {data}")
                    data= dm.add_project(data, project)

                # Does the current entity have a project_session if not initialise it
                elif not ntt.is_project_session_exist(data, entity, self.core):
                    session = di.initialise_project_sessions(entity, start_time)
                    data = dm.add_project_session(data, session, entity)

                else:
                    session = di.initialise_asset_session(start_time)
                    data = dm.add_asset_session(data, entity, session)
                
                # Set last active project and set last file opened etc
                data_last = dm.update_last(data_last, entity)
                log(f"new data_last = {data_last}")

                # Set last datas
                log(f"current_data = {data}")
                log(f"current user = {user}")
                data['user_id'] = user
                data['year'] = str(year)
                data['week'] = str(week)
                data['week_description'] = week_description

                # Write data to file
                js_obj = json.dumps(data)
                content = "var data = '{}'".format(js_obj)
                file.write_to_file(content, mhfx_path.user_data_js)

                json_obj = json.dumps(data, indent=4)
                file.write_to_file(json_obj, mhfx_path.user_data_json)

                json_last_obj = json.dumps(data_last, indent=4)
                file.write_to_file(json_last_obj, mhfx_path.user_last_json)
                
                
            except Exception as e:
                log(traceback.format_exc())

            log('done create data')

    def update_data(self, entity):
        '''
        Get data from hours.js and last.json
        If current asset is not last opened asset : create new data
        Change data according the entity currently open
        Write in hours.json, hours.js, last.json and last.js

        :param entity: dict
        '''

        if 'noUI' not in self.core.prismArgs:

            now = datetime.now()
            date = now.strftime('%d/%m/%y')

            # Get data from file
            try:
                # Open user json data and laod it to data
                data = file.get_data(mhfx_path.user_data_json)
            except:
                # If json file empty return empty dict/json object
                self.create_data(entity)

            try:
                # verify if still the same asset
                last = file.get_data(mhfx_path.user_last_json)
                if ntt.is_same_asset(entity, last):

                    # update session
                    days = data.get('days')

                    for d in days:
                        if d.get('date') ==  date:
                            project = ntt.get_current_project(self.core)
                            projects = d.get('projects')
                            for p in projects:
                                if p.get('project_name') == project:
                                    project_sessions = p.get('project_sessions')
                                    for ps in project_sessions:
                                        asset_name = ps.get('asset_name')
                                        department = ps.get('department')
                                        if asset_name == entity.get('asset_name') and department == entity.get('department'):
                                            total_time = timedelta(seconds=0)
                                            sessions = ps.get('asset_sessions')

                                            # update last action time
                                            sessions[-1]['last_action_time'] = now.strftime('%H:%M:%S')
                                            # update total_time session
                                            delta = dt.get_date_delta(now, sessions[-1].get('start_time'))
                                            sessions[-1]['total_time'] = str(delta)
                                        
                                            # update total_time project session
                                            for s in sessions:
                                                tt = dt.get_time_as_datetime_obj(s.get('total_time'))
                                                delta_tt = timedelta(hours=tt.hour, minutes=tt.minute, seconds=tt.second)
                                                total_time += delta_tt
                                            ps['total_time'] = str(total_time)
                                            break

                    # Write data to file
                    js_obj = json.dumps(data)
                    content = "var data = '{}'".format(js_obj)
                    file.write_to_file(content, mhfx_path.user_data_js)

                    json_obj = json.dumps(data, indent=4)
                    file.write_to_file(json_obj, mhfx_path.user_data_json)

                else:
                    self.create_data(entity)

            except Exception as e:
                log(traceback.format_exc())

            log('done update')

         
# CALLBACKS
    def onSceneOpen(self, *args):
        log("scene opened")
        log(f"args = {args}")
        if args[0] != 'unknown' and self.is_disk_allowed(args[0]):
            entity = ntt.get_entity(self.core)
            log(f"entity= {entity}")
            if entity:
                self.create_data(entity)

            else:   
                log(f"entity empty")
        else:
            log(f"disk not  allowed")

    def update_callback(self, cll_name, *args):
        log(cll_name)
        entity = ntt.get_entity(self.core)
        log(f"entity= {entity}")
        if entity:
            self.update_data(entity)
        else:            
            log(f"entity empty")
