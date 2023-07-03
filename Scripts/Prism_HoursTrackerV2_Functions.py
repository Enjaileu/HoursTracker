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
import threading

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

from utils.config import mhfx_path, mhfx_disk, monitor
import utils.entity as ntt
from utils.mhfx_log import log
import utils.date as dt
import utils.data_management as dm
import utils.data_initialise as di
import utils.file as file
from Monitor import Monitor
from Process import Process
from utils.windows import get_pid_by_process_name


class Prism_HoursTrackerV2_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.version = self.core.version.split('.', 3)[-1]

        try:
            # Verify and create filepath
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

        except Exception as e:
            log(traceback.format_exc())
            log(str(e))


        # Initialise Monitor
        self.monitor = Monitor()

        self.thread = threading.Thread(target=self.monitor.run)

        # replace function openFile
        self.core.plugins.monkeyPatch(self.core.openFile, self.openFile, self, force=True)
        self.core.plugins.monkeyPatch( self.core.appPlugin.openScene, self.plugin_openScene, self, force=True)

        # callback
        self.core.callbacks.registerCallback("onFileOpen", self.onFileOpen, plugin=self)


    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
# MONKEY PATCH
    def openFile(self, filepath):
        log(f"open file {filepath}")
        self.core.plugins.callUnpatchedFunction(self.core.openFile, filepath)
        self.core.callback(name="onFileOpen", args=[filepath])

    def plugin_openScene(self, *args):
        log(f"open from plugin file {args[1]}")
        log(f"args = {args}")
        self.core.plugins.callUnpatchedFunction(self.core.appPlugin.openScene, origin=args[0], filepath=args[1])
        self.core.callback(name="onFileOpen", args=[args[1]])

# CALLBACK
    
    def onFileOpen(self, *args):
        filepath = args[0]
        log(f"FILEPATH GIVEN : {filepath}")
        try:
            data = file.get_data(mhfx_path.user_data_json)
            now = datetime.now()
            week = now.isocalendar()[1]
            # Check if it's a new week, archive and reset data if it is
            if dt.is_new_week(data, week) is True:
                file.backup_data(data)
                file.reset_user_data()

            # get ext, exe and pid
            filepath = Path(filepath)
            ext = filepath.suffix
            exe = []
            for extension in monitor.executables.keys():
                if extension == ext:
                    exe = monitor.executables.get(extension)
                    break
            
            if len(exe) <= 0:
                log(f"soft with this ext : {ext} is not in config")
                log(f"if this extension is a ddc extension, please add it in config.")
            else:
                pid = get_pid_by_process_name(exe)
            
                # Add process to monitor
                self.monitor.add_process(filepath, exe, pid)
                log(f"open this file : {filepath}, in this executable : {str(exe)}, with this pid {pid}")

                # Start Monitor if not running
                if self.monitor.is_running == False:
                    self.monitor.start_thread()

            
        except Exception as e:
            log(traceback.format_exc())
            log(str(e))
        