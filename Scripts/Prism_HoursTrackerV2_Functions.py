# Author: Elise Vidal
# Contact :  evidal@artfx.fr

# Author: Angèle Sionneau
# Contact :  asionneau@artfx.fr

import os
import shutil
import traceback
from datetime import datetime
from pathlib import Path

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

from monitor_utils.config import mhfx_path, mhfx_exe, monitor
import monitor_utils.file as file
from Monitor import Monitor
from monitor_utils.mhfx_log import log

class Prism_HoursTrackerV2_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.prism_version = f"{self.core.version.split('.', 3)[-1]}"

        try:
            # Verify and create filepath
            if not os.path.exists(mhfx_path.user_data_dir):
                os.makedirs(mhfx_path.user_data_dir)

            if not os.path.exists(mhfx_path.user_tmp_dir):
                os.makedirs(mhfx_path.user_tmp_dir)
            
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

            if not os.path.exists(mhfx_path.user_data_js):
                open(mhfx_path.user_data_js, 'a').close()
            
            if not os.path.exists(mhfx_path.user_config):
                src = f'R:/Prism/Plugins/{self.prism_version}/HoursTrackerV2/Scripts/templates/config.ini'
                dst = mhfx_path.user_config
                shutil.copy(src, dst)
            
            if not os.path.exists(mhfx_path.user_data_html):
                src = f'R:/Prism/Plugins/{self.prism_version}/HoursTrackerV2/Scripts/templates/hours.html'
                dst = mhfx_path.user_data_html
                shutil.copy(src, dst)

            if not os.path.exists(mhfx_path.user_data_css):
                src = f'R:/Prism/Plugins/{self.prism_version}/HoursTrackerV2/Scripts/templates/style.css'
                dst = mhfx_path.user_data_css
                shutil.copy(src, dst)

            if not os.path.exists(mhfx_path.user_tmp_processes):
                with open(mhfx_path.user_tmp_processes, 'a') as json_file:
                    json_file.write('{}')

            if not os.path.exists(mhfx_path.user_tmp_last_proc):
                with open(mhfx_path.user_tmp_last_proc, 'a') as json_file:
                    json_file.write('{}')

            # Initialise Monitor
            self.monitor = Monitor()

            # replace function openFile
            self.core.plugins.monkeyPatch(self.core.openFile, self.openFile, self, force=True)
            self.core.plugins.monkeyPatch( self.core.appPlugin.openScene, self.plugin_openScene, self, force=True)
            self.core.plugins.monkeyPatch( self.core.onExit, self.onExit, self, force=True)

            # callback
            self.core.callbacks.registerCallback("onFileOpen", self.onFileOpen, plugin=self)
        except Exception as e:
            log(traceback.format_exc())


    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
    
# MONKEY PATCH
    def openFile(self, filepath):
        '''
        Override function self.core.openFile.
        Use the overriden function then add callback "onFileOpen"
        '''
        pid = -1
        self.core.plugins.callUnpatchedFunction(self.core.openFile, filepath)
        self.core.callback(name="onFileOpen", args=[filepath, pid])


    def plugin_openScene(self, origin, filepath, force=True):
        '''
        Ovveride function self.core.appPlugin.openScene.
        Use the overriden function then add callback "onFileOpen".
        '''
        
        # get current pid
        pid = os.getpid()
        
        try:

            # check if current scene is empty scene
            empty_scene = False
            current_file = self.core.getCurrentFileName()
            
            if current_file == 'unknown' or current_file == None or current_file =='':
                empty_scene = True

            # get file extensions
            current_ext = Path(current_file).suffix
            current_exe = mhfx_exe.executables.get(current_ext)
            want_ext = Path(filepath).suffix
            want_exe = mhfx_exe.executables.get(want_ext)

            # get the plugin name
            plugin_name = self.core.appPlugin.pluginName

            if monitor.debug_mode:
                log(f"current_file = {current_file}")
                log(f"wanted_file = {filepath}")
                log(f"Try to open with {plugin_name}")

            # if current scene is empty scene
            if empty_scene == True:
                
                if plugin_name in ['Photoshop', 'SubstancePainter']:
                    if plugin_name == 'Photoshop' and want_ext not in ['.psd']:
                        if monitor.debug_mode:
                            log(f"User try to open file with extension {want_ext} in Photoshop : Fail.")
                        return
                    elif plugin_name == 'SubstancePainter' and want_ext not in ['.spp']:
                        if monitor.debug_mode:
                            log(f"User try to open file with extension {want_ext} in SubstancePainter : Fail.")
                        return
                
                if Path(filepath).suffix != '':
                    is_openning = self.core.plugins.callUnpatchedFunction(self.core.appPlugin.openScene, origin=origin, filepath=filepath, force=force)
                    if is_openning == True:
                        self.core.callback(name="onFileOpen", args=[filepath, pid])
            elif current_exe == want_exe:
                # ask for saving action if not empty scene
                answers = ["Save", "Don't Save", "Cancel"]
                option = self.core.popupQuestion(text = "Save Changes ?", title="Open new scene", buttons=answers )
                if monitor.debug_mode:
                    log(f"User choose '{option}'")
                # user want to save
                if option == answers[0]:
                    self.core.saveScene(filepath=current_file)
                    is_openning = self.core.plugins.callUnpatchedFunction(self.core.appPlugin.openScene, origin=origin, filepath=filepath, force=force)
                    if is_openning == True:
                        self.core.callback(name="onFileOpen", args=[filepath, pid])
                # user want to open but not save current scene
                elif option == answers[1]:
                    is_openning = self.core.plugins.callUnpatchedFunction(self.core.appPlugin.openScene, origin=origin, filepath=filepath, force=force)
                    if is_openning == True:
                        self.core.callback(name="onFileOpen", args=[filepath, pid])
                # cancel -> do noting

        except Exception as e:
            log(str(e))
        


    def onExit(self):
        '''
        Override the PrismCore.onExit method. Before exit Prism, ask to the monitor to save its Process data.
        '''
        self.saveForceProcess()
        self.core.plugins.callUnpatchedFunction(self.core.onExit)
        
# FUNCTION
    def is_new_week(self, data, week):
        """
        Check if the current week is different from the week store in data

        :param data: dict
        :param week: int
        :return: bool
        """
        if data == {} or data == None:
            return True
        last_week = data.get('week')
        return last_week != str(week)

    def is_new_day(self, data: dict, date: str):
        '''
        Checks if the given date exists in the data

        :param data: dict
        :param date: string
        :return: bool
        '''
        try:

            if data == {} or data == None:
                return True
            for d in data.get('days'):
                log(f"{d.get('date')} == {date} : {d.get('date') == date}")
                if d.get('date') == date:
                    return False
            return True
        except Exception as e:
            log(traceback.format_exc())

# CALLBACK
    def onFileOpen(self, *args):
        '''
        Executed when the callback "onFileOpen" is called.
        Get the filepath openend and if allowed software, add it as process to monitor.

        :param args: list, args[0] = filepath
        '''
        filepath = ''.join(args[0])
        pid = args[1]
        if filepath != 'Tools':
            if monitor.debug_mode:
                log('////////////////////////////////////////////////////////////////////////////////////////')
                log(f"Prism open file with monitor {self.monitor.id} : {filepath} ")
                log(f"...from Prism {str(self.core.appPlugin.pluginName)}")
            try:
                data = file.get_data(mhfx_path.user_data_json)
                now = datetime.now()
                week = now.isocalendar()[1]
                date = now.strftime('%d/%m/%y')
                # Check if it's a new week, archive and reset data if it is
                if self.is_new_week(data, week) is True:
                    if monitor.debug_mode:
                        log("New week")
                    file.backup_data(data)
                    file.reset_user_data()
                    self.monitor.saveClosedProcess(False)
                # Check if it's new day, reset processes data if it's true
                elif self.is_new_day(data, date):
                    if monitor.debug_mode:
                        log("New day")
                    self.monitor.saveClosedProcess(False)

                # get extension and executable
                filepath = Path(filepath)
                ext = filepath.suffix.lower()
                exe = []
                if ext in mhfx_exe.executables.keys():
                    exe = mhfx_exe.executables.get(ext)

                # Add process if a executable is found
                if len(exe) <= 0:
                    log(f"soft with this ext : {ext} is not in config")
                    if monitor.debug_mode:
                        log(f"if this extension is a ddc extension, please add it in mhfx_utils.config.mhfx_exe.py")
                else:
                    # Add process to monitor
                    self.monitor.add_process(filepath, exe, pid)

                if monitor.debug_mode: 
                    log('////////////////////////////////////////////////////////////////////////////////////////')

                    # Start Monitor if not running
                    if self.monitor.is_running == False:
                        self.monitor.start_thread()

            except:
                log(traceback.format_exc())

    def saveForceProcess(self, *args):
        if str(self.core.appPlugin.pluginName) != "Standalone":
            try:
                if monitor.debug_mode:
                    fn = self.core.getCurrentFileName()
                    log(f'saveForceProcess for monitor {self.monitor.id}')
                self.monitor.saveClosedProcess(True)
            except Exception as e:
                log(str(e))