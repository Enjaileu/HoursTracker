# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2021 Richard Frangenberg
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.

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
import PrismCore



class Prism_HoursTrackerV2_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        version = self.core.version.split('.', 3)[-1]

        # Register callback functions
        self.core.callbacks.registerCallback(
            "onSceneOpen", self.onSceneOpen, plugin=self)
        self.core.callbacks.registerCallback(
            "sceneSaved", self.sceneSaved, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateManagerShow", self.onStateManagerShow, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateManagerClose", self.onStateManagerClose, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateDeleted", self.onStateDeleted, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateCreated", self.onStateCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onPublish", self.onPublish, plugin=self)
        self.core.callbacks.registerCallback(
            "postPublish", self.postPublish, plugin=self)
        self.core.callbacks.registerCallback(
            "onProductCreated", self.onProductCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onAssetCreated", self.onAssetCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onShotCreated", self.onShotCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onDepartmentCreated", self.onDepartmentCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onTaskCreated", self.onTaskCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "postExport", self.postExport, plugin=self)

        # Check if exists/create on disk data files
        self.user_data_dir = 'U:/mesDocuments/HoursTrackerV2/'
        self.user_data_json = self.user_data_dir + 'hours.json'
        self.user_data_js = self.user_data_dir + 'hours.js'
        self.user_data_html = self.user_data_dir + 'hours.html'
        self.user_data_css = self.user_data_dir + 'style.css'
        self.user_data_backup = self.user_data_dir + 'backup/'
        self.user_list_backup_json =  self.user_data_dir + 'backups.json'
        self.user_list_backup_js =  self.user_data_dir + 'backups.js'
        self.user_log = self.user_data_dir + 'log.txt'

        
        if not os.path.exists(self.user_log):
            open(self.user_log, 'a').close()

        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

        if not os.path.exists(self.user_data_backup):
            os.makedirs(self.user_data_backup)

        if not os.path.exists(self.user_list_backup_json):
            with open(self.user_list_backup_json, 'a') as json_file:
                json_file.write('{}')

        if not os.path.exists(self.user_list_backup_js):
            open(self.user_list_backup_js, 'a').close()

        if not os.path.exists(self.user_data_json):
            with open(self.user_data_json, 'a') as json_file:
                json_file.write('{}')

        if not os.path.exists(self.user_data_js):
            open(self.user_data_js, 'a').close()
        

        if not os.path.exists(self.user_data_html):
            src = 'R:/Prism/Plugins/{version}/HoursTracker/Scripts/templates/hours.html'.format(version=version)
            dst = self.user_data_html
            shutil.copy(src, dst)

        if not os.path.exists(self.user_data_css):
            src = 'R:/Prism/Plugins/{version}/HoursTracker/Scripts/templates/style.css'.format(version=version)
            dst = self.user_data_css
            shutil.copy(src, dst)

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
        
        if path[0] == 'C':
            return False
        return True

#pragma region initialise

    def initialise_data(self, date, entity, start_time):
        '''
        Initialise complete data template of tracking hours

        :param date: date of the day
        :param entity: entity of the asset opened
        :param start_time: time when the asset was opened
        :return: dict 
        '''
        
        data = {
            "days":[ self.initialise_day(date, entity, start_time)]
        }
        return data
    
    def initialise_day(self, date, entity, start_time):
        '''
        Initialise a new day to append to the data

        :param date: date of the day
        :param entity: entity of the asset opened
        :param start_time: time when the asset was opened
        :return: dict 
        '''
        return {"date": date, "projects": [self.initialise_project(entity, start_time)]}
    
    def initialise_project(self, entity, start_time):
        '''
        Initialise a new project to append to the date in the data

        :param entity: entity of the asset opened
        :param start_time: time when the asset was opened
        :return: dict
        '''
        try:
            project = {
                'project_name': self.get_current_project(),
                'project_sessions':[self.initialise_project_sessions(entity, start_time)]
            }
            return project
        except Exception as e:
            self.log(traceback.format_exc())
        
    def initialise_project_sessions(self, entity, start_time):
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
                'asset_sessions': [self.initialise_asset_session(start_time)],
                'total_time': '0:00:00'
            }
            return sessions
        except Exception as e:
            self.log(traceback.format_exc())

    def initialise_asset_session(self, start_time):
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
            self.log(traceback.format_exc())
#pragma endregion initialise

#pragma region dates

    def get_date_as_datetime_obj(self, date_string):
        '''
        Converts a string object representing a date, like this %d/%m/%y, to a datetime object
        returns: datetime
        '''
        datetime_obj = datetime.strptime(date_string, '%d/%m/%y')
        return datetime_obj

    def get_time_as_datetime_obj(self, time_string):

        return datetime.strptime(time_string,'%H:%M:%S')

    def get_date_as_string(self, datetime_obj):
        '''
        Converts datetime object to string format %d/%m/%y.
        Returns: string
        '''
        date_string = datetime_obj.strftime('%d/%m/%y')
        return date_string

    def get_date_delta(self, newest_date, oldest_date):
        """
            Returns a timedelta object of two giving dates.
            Checks and converts if necessarey to datetime format before
            calculating delta

            newest_date: str or datetime
            oldest_date: str or datetime
        """
        try:
            return newest_date - oldest_date
        except TypeError:
            try:
                newest_date = self.get_time_as_datetime_obj(newest_date)
            except TypeError:
                pass
            try:
                oldest_date = self.get_time_as_datetime_obj(oldest_date)
            except TypeError:
                pass

            delta = timedelta(hours=newest_date.hour, minutes=newest_date.minute, seconds=newest_date.second) - timedelta(hours=oldest_date.hour, minutes=oldest_date.minute, seconds=oldest_date.second)
            self.log(f"delta = {delta}")
            return  delta

    def is_new_week(self, data, week):
        """
        """
        last_week = data.get('week')
        self.log(f'last week = {last_week}, week = {str(week)}')
        return last_week != str(week)

    def get_week_definition(self):
        # Get the Monday and Wednesday dates for the given week number and year
        today = datetime.now()

        day_of_week = today.weekday()

        to_beginning_of_week = timedelta(days=day_of_week)
        monday = today - to_beginning_of_week

        to_end_of_week = timedelta(days=4 - day_of_week)
        wednesday = today + to_end_of_week

        mon = self.get_date_as_string(monday)
        wed = self.get_date_as_string(wednesday)

        return f"{mon} - {wed}"

    def get_last_week_definition(self):
        # Get the Monday and Wednesday dates for the given week number and year
        last_week = datetime.now() - timedelta(days=7)

        day_of_week = last_week.weekday()

        to_beginning_of_week = timedelta(days=day_of_week)
        monday = last_week - to_beginning_of_week

        to_end_of_week = timedelta(days=4 - day_of_week)
        wednesday = last_week + to_end_of_week

        mon = self.get_date_as_string(monday)
        wed = self.get_date_as_string(wednesday)

        return f"{mon} - {wed}"
#pragma endregion dates

#pragma region entity

    def get_username(self):
        '''
        Returns the user's name
        '''
        try:
            return self.core.getConfig("globals", "username")
        except:
            return self.core.username

    
    def get_entity(self):
        try :
            file_name = self.core.getCurrentFileName()
            data = self.core.getScenefileData(file_name)
            if data == {}:
                self.log('no data linked to this asset')
                return {}
            else:
                entity = {
                    'name': data.get('filename'),
                    'department': data.get('task'),
                    'asset_type': data.get('type'),
                    'project_name': self.get_current_project()
                }

                if entity.get('asset_type') == 'shot':
                    entity['asset_name'] = f"{data.get('sequence')}_{data.get('shot')}"
                else:
                    entity['asset_name'] = data.get('asset')

                return entity
        except Exception as e:
            self.log(traceback.format_exc())
            return {}
            
    def get_current_project(self):
        '''
        Returns the project's name
        '''
        try:
            project_name = self.core.projectName
        except:
            project_path = self.core.getConfig("globals", "current project")
            project_name = os.path.basename(os.path.dirname(os.path.dirname(project_path)))

        return project_name
#pragma endregion entity

#pragma region file
   
    def get_data(self, path):
        path = str(path)
        try:
            # Open user json data and laod it to data
            with open(path, 'r') as json_file:
                raw_data = json_file.read()
                data = json.loads(raw_data)
        except Exception as e:
            self.log(traceback.format_exc())
            # If json file empty return empty dict/json object
            data = {}
        
        return data

    def write_to_file(self, content, filename):
        '''
        Writes given content to the given filename.
        '''
        output_file = open(filename, 'w')
        output_file.write(content)
        output_file.close()
    
    def backup_data(self, week, year):
        """
        Copies the user's json data to a backup location
        """
        # last week and last year
        week = week-1
        if week==0:
            year -= 1
            week = 52

        # write hours data
        src = self.user_data_json
        dst = f"{self.user_data_backup}{week}_{year}_hours.json"
        shutil.copy(src, dst)

        src = self.user_data_js
        dst = f"{self.user_data_backup}{week}_{year}_hours.js"
        shutil.copy(src, dst)

        src = self.user_log
        dst = f"{self.user_data_backup}{week}_{year}_log.txt"
        shutil.copy(src, dst)

        # write backup data
        new_bckp = self.create_backup_info(week, year)
        bckp_info = self.get_data(self.user_list_backup_json)
        if bckp_info == {}:
            bckp_info = {"backups":[]}
        bckp_info.get('backups').insert(0, new_bckp)

        js_obj = json.dumps(bckp_info)
        content = f"var data = '{js_obj}'"
        self.write_to_file(content, self.user_list_backup_js)

        json_obj = json.dumps(bckp_info, indent=4)
        self.write_to_file(json_obj, self.user_list_backup_json)

        self.write_to_file('', self.user_log)
    
    def reset_user_data(self):
        """
        Resets the json file containing the user's data
        """
        with open(self.user_data_json, 'a') as json_file:
                json_file.write('{}')

    def create_backup_info(self,week, year):
        bkp = {
            "week": str(week),
            "year": str(year),
            "path": f"{self.user_data_backup}{week}_{year}_hours.js",
            "week_description": self.get_last_week_definition()
        }

        return bkp
#pragma endregion file

#pragma region modify_data

    def update_last(self, data, entity):
        data['last_active_project'] = self.get_current_project()
        data['last_opened'] = entity.get('asset_name')

    def add_project(self, data, project):
        data.get('days')[-1].get('projects').append(project)

    def add_project_session(self, data, entity, session):
        projects = data.get('days')[-1].get('projects')
        for p in projects:
            if p.get('project_name') == self.get_current_project():
                p.get('project_sessions').append(session)
    
    def add_asset_session(self, data, entity, session):
        projects = data.get('days')[-1].get('projects')
        for p in projects:
            if p.get('project_name') == self.get_current_project():
                project_sessions = p.get('project_sessions')
                for ps in project_sessions:
                    if ps.get('asset_name') == entity.get('asset_name') and ps.get('department') == entity.get('department'):
                        ps.get('asset_sessions').append(session)
                        self.log('asset session added')
#pragme enregion modify_data

#pragma region check_data
    def does_day_exist(self, data, date):
        try:
            for d in data.get('days'):
                if d.get('date') == date:
                    return True
        except Exception as e:
                self.log(traceback.format_exc())    

    def does_project_exist(self, data):
        try:
            project = self.get_current_project()
            projects = data.get('days')[-1].get('projects')
            for p in projects:
                if p.get('project_name') == project:
                    return True

        except Exception as e:
                self.log(traceback.format_exc())

    def is_project_session_exist(self, data, entity):
        projects = data.get('days')[-1].get('projects')
        for p in projects:
            if p.get('project_name') == self.get_current_project()
                sessions = p.get('project_sessions')
                for s in sessions:
                    if s.get('asset_name') == entity.get('asset_name') and s.get('department') == entity.get('department'):
                        return True
        
        return False
#pragma endregion check_data

    
    def log(self, error_message):
        date = datetime.now().strftime('%d/%m/%y')
        time = datetime.now().strftime('%H:%M:%S')
        log_message = '\n' + date + ", " + time + " : " + error_message
        with open(self.user_log, 'a') as logfile:
            logfile.write(log_message)
  

# LOGIC
    def create_data(self, entity={}):
        """
        Function that runs everytime a callback is called in Prism. The logic happens here.
        Retrieves user date from file
        Creates data relevant to the scene opening action: user, date, time
        Runs a series of checks on existing data to determine where to write the action's data
        Writes the action's data
        """
        if 'noUI' not in self.core.prismArgs:
            try:
                # Get scene open action relevant data
                user = self.get_username()
                now = datetime.now()
                date = now.strftime('%d/%m/%y')
                start_time = now.strftime('%H:%M:%S')
                year = now.isocalendar()[0]
                week = now.isocalendar()[1]
                week_description = self.get_week_definition()

                # Get data from file
                try:
                    # Open user json data and laod it to data
                    data = self.get_data(self.user_data_json)
                except:
                    # If json file empty return empty dict/json object
                    data = {}

                
                # If data is empty initialise it
                if data == {}:
                    data = self.initialise_data(date, entity, start_time)
                
                # Check if it's a new week, archive and reset data if it is
                elif self.is_new_week(data, week) is True:
                    self.backup_data(week, year)
                    data = {}
                    self.reset_user_data()
                    data = self.initialise_data(date, entity, start_time)
                

                # Check if current day exists and create data if necessary
                elif not self.does_day_exist(data, date):
                    new_day = self.initialise_day(date, entity, start_time)
                    data.get('days').append(new_day)
                    self.update_last(data, entity)
                    

                # Does the current project exist for today date, if not initialise it
                elif not self.does_project_exist(data):
                    project = self.initialise_project(entity, start_time)
                    self.add_project(data, project)
                    self.update_last(data, entity)

                # Does the current entity have a project_session if not initialise it
                elif not self.is_project_session_exist(data, entity):
                    session = self.initialise_project_sessions(entity, start_time)
                    self.add_project_session(data, entity, session)
                    self.update_last(data, entity)

                # TODO : else, add sesssion
                else: 
                    session = self.initialise_asset_session(start_time)
                    self.add_asset_session(data, entity, session)
                
                # Set last active project and set last file opened
                self.update_last(data, entity)

                # Set last datas
                data['user_id'] = user
                data['year'] = str(year)
                data['week'] = str(week)
                data['week_description'] = week_description

                # Write data to file
                js_obj = json.dumps(data)
                content = "var data = '{}'".format(js_obj)
                self.write_to_file(content, self.user_data_js)

                json_obj = json.dumps(data, indent=4)
                self.write_to_file(json_obj, self.user_data_json)
                
                
            except Exception as e:
                self.log(traceback.format_exc())

            self.log('done')

    def update_data(self, entity):

        now = datetime.now()
        date = now.strftime('%d/%m/%y')

    # Get data from file
        try:
            # Open user json data and laod it to data
            data = self.get_data(self.user_data_json)
        except:
            # If json file empty return empty dict/json object
            self.log('data doesnt exist')
            self.create_data(entity)


        try:
            # update session
            days = data.get('days')

            for d in days:
                if d.get('date') ==  date:
                    project = self.get_current_project()
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

                                    # update last action time
                                    sessions[-1]['last_action_time'] = now.strftime('%H:%M:%S')
                                    # update total_time session
                                    delta = self.get_date_delta(now, sessions[-1].get('start_time'))
                                    sessions[-1]['total_time'] = str(delta)
                                
                                    # update total_time project session
                                    for s in sessions:
                                        tt = self.get_time_as_datetime_obj(s.get('total_time'))
                                        delta_tt = timedelta(hours=tt.hour, minutes=tt.minute, seconds=tt.second)
                                        total_time += delta_tt
                                    ps['total_time'] = str(total_time)

                                    self.log('session updated')
                                    break

            self.log(str(data))
            # Write data to file
            js_obj = json.dumps(data)
            content = "var data = '{}'".format(js_obj)
            self.write_to_file(content, self.user_data_js)

            json_obj = json.dumps(data, indent=4)
            self.write_to_file(json_obj, self.user_data_json)

        except Exception as e:
            self.log(traceback.format_exc())

        self.log('done update')

         

# CALLBACKS
    '''
    To add new callbacks:
    1. Register the callback in the init() function
    2. Add a definition for the  callback function below, make sure it call self.update_data()
    3. Check in the Prism source code if the callback accepts *args and/or **kwargs (to avoid Prism Errors that can't be caught)
    '''
    def onSceneOpen(self, *args):
        self.log("scene saved")
        if args[0] and self.is_disk_allowed(args[0]):
            entity = self.get_entity()
            if entity:
                self.create_data(entity)
            else:   
                self.log(f"entity empty")
            
    def sceneSaved(self, *args):
        self.log("scene saved")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onStateManagerShow(self, *args):
        self.log("state manager opened")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onStateManagerClose(self, *args):
        self.log("state manager closed")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onStateDeleted(self, *args):
        self.log("state deleted")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onStateCreated(self, *args, **kwargs):
        self.log("state created")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onPublish(self, *args):
        self.log("on publish")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def postPublish(self, *args, **kwargs):
        self.log("post_published")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onProductCreated(self, *args):
        self.log("product created")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onAssetCreated(self, *args):
        self.log("asset created")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onShotCreated(self, *args):
        self.log("shot created")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onDepartmentCreated(self, *args):
        self.log("department created")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def onTaskCreated(self, *args):        
        self.log("task created")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")

    def postExport(self, **kwargs):
        self.log("post export")
        entity = self.get_entity()
        if entity:
            self.update_data(entity)
        else:            
            self.log(f"entity empty")
