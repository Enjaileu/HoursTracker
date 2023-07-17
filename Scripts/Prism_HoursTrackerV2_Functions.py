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
from monitor_utils.mhfx_log import log
import monitor_utils.file as file
from Monitor import Monitor

class Prism_HoursTrackerV2_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        # TODO : change
        #self.version = self.core.version.split('.', 3)[-1]
        self.prism_version = f"{self.core.version.split('.', 3)[-1]}.test"

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

            # Initialise Monitor
            self.monitor = Monitor()

            # replace function openFile
            self.core.plugins.monkeyPatch(self.core.openFile, self.openFile, self, force=True)
            self.core.plugins.monkeyPatch( self.core.appPlugin.openScene, self.plugin_openScene, self, force=True)

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
        self.core.plugins.callUnpatchedFunction(self.core.openFile, filepath)
        self.core.callback(name="onFileOpen", args=[filepath])

    def plugin_openScene(self, origin, filepath, force=False):
        '''
        Ovveride function self.core.appPlugin.openScene.
        Use the overriden function then add callback "onFileOpen".
        '''
        self.core.plugins.callUnpatchedFunction(self.core.appPlugin.openScene, origin=origin, filepath=filepath, force=force)
        self.core.callback(name="onFileOpen", args=filepath)

# FUNCTION
    def is_new_week(self, data, week):
        """
        Check if the current week is different from the week store in data

        :param data: dict
        :param week: int
        :return: bool
        """
        if data == {}:
            return False
        last_week = data.get('week')
        return last_week != str(week)

# CALLBACK
    def onFileOpen(self, *args):
        '''
        Executed when the callback "onFileOpen" is called.
        Get the filepath openend and if allowed software, add it as process to monitor.

        :param args: list, args[0] = filepath
        '''
        filepath = ''.join(args)
        if filepath != 'Tools':
            if monitor.debug_mode:
                log(f"Prism open file : {filepath}")
            try:
                data = file.get_data(mhfx_path.user_data_json)
                now = datetime.now()
                week = now.isocalendar()[1]
                # Check if it's a new week, archive and reset data if it is
                if self.is_new_week(data, week) is True:
                    file.backup_data(data)
                    file.reset_user_data()

                # get extension and executable
                filepath = Path(filepath)
                ext = filepath.suffix
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
                    self.monitor.add_process(filepath, exe)

                    # Start Monitor if not running
                    if self.monitor.is_running == False:
                        self.monitor.start_thread()
            except:
                log(traceback.format_exc())
        