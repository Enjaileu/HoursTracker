from threading import Thread
from time import sleep
import json
import traceback

from Process import Process, Path, Status
from utils.config import monitor, mhfx_path
from utils.windows import get_current_window, get_entity, does_process_exists
from utils.file import get_data
from utils.data_management import update_data
import utils.file as file
from utils.mhfx_log import log

class Monitor(object):
    def __init__(self):
        self.is_running = False
        self.processes = []
        self.thread = None
        self.cycle_incr = 0

    def start_thread(self):
        log("start thread")
        try:
            if self.thread == None:
                self.thread = Thread(target=self.run)
            else:
                self.thread.join()
            
            self.thread = Thread(target=self.run)
            self.is_running = True
            self.thread.start()
        
        except Exception as e:
            log(traceback.format_exc())
    
    def stop_thread(self):
        try:
            self.update_data()
            self.is_running = False
        except Exception as e:
            log(traceback.format_exc())
            log(str(e))
    
    def add_process(self, filename: Path, executable: str, pid: int):
        '''
        Create an object Process and add it in self.processes
        If pid already exists, don't add it and change initial proc infos. 

        :param filename: pathlib.Path
        :param executables: str, from config.monitor.executables
        :param pid: int
        '''
        try:
            log(f"Try to add process with filename: {str(filename)}, exe: {executable}, pid: {pid}")
            proc = self.check_duplicate_pid(pid)
            if proc == None:
                log('add process')
                proc = Process(filename, executable, pid)
                self.processes.append(proc)
            else:
                log('pid already exists')
                self.update_data()
                proc.filename= filename
                proc.executable = executable

            log('processes : ')
            for p in self.processes:
                log(str(p))

        except Exception as e:
            log(traceback.format_exc())
            log(str(e))

    def remove_process(self, pid: int):
        try:
            for proc in self.processes:
                if proc.pid == pid:
                    self.processes.remove(proc)
                    break
        except Exception as e:
            log(traceback.format_exc())
            log(str(e))

    def run(self):
        while self.is_running:
            log('###############################################')
            log(f'go wait for {monitor.wait_sec} sec')
            wait_sec = monitor.wait_sec
            sleep(wait_sec)
            closed_proc = 0
            for proc in self.processes:
                if not does_process_exists(proc.pid):
                    closed_proc +=1
            if len(self.processes) <= closed_proc:
                log('all the proc are closed')
                self.stop_thread()
                self.processes = []
            else:
                wndw = get_current_window()
                log(f"current window = {str(wndw)}")
                index = next((index for index, proc in enumerate(self.processes) if proc.pid == wndw.get('pid')), None)
                if index != None:
                    log(f"window already in processes")
                    self.processes[index].time += wait_sec
                    self.processes[index].status == Status.ACTIVE
                    log(f"After change = \n{self.processes[index]}")
                #TODO : add afk_sec sur tous les proc INACTIVE

                self.cycle_incr += wait_sec
                if self.cycle_incr >= monitor.total_cycle:
                    log("~~~~~~~~~~~~ cycle finished!! ~~~~~~~~~~~~")
                    self.cycle_incr = 0
                    self.update_data()
                    


    def update_data(self):
        log("update data")
        data = get_data(mhfx_path.user_data_json)
        processes_copy = self.processes
        for proc in processes_copy:
            # ACTIVE
            if proc.status == Status.ACTIVE:
                log("proc active")
                entity = get_entity(proc.filename)
                data = update_data(data, entity, proc.time, proc.first)
                proc.status == Status.INACTIVE
            # OLD
            elif proc.status == Status.OLD:
                log("proc old")
                if not does_process_exists(proc.pid):
                    entity = get_entity(proc.filename)
                    data = update_data(data, entity, proc.time, proc.first)
                    self.remove_process(proc.pid)
            # INACTIVE
            else:
                log("proc inactive")
                proc.afk_sec += monitor.total_cycle
                log(f"afk_sec de {proc.pid} = {proc.afk_sec}")
                if proc.afk_sec >= monitor.max_afk_cycle:
                    log("proc inactive depuis trop longtemps")
                    entity = get_entity(proc.filename)
                    data = update_data(data, entity, proc.time, proc.first)
                    proc.status == Status.OLD
        log(f"new data = {data}")
        
        js_obj = json.dumps(data)
        content = "var data = '{}'".format(js_obj)
        file.write_to_file(content, mhfx_path.user_data_js)

        json_obj = json.dumps(data, indent=4)
        file.write_to_file(json_obj, mhfx_path.user_data_json)
    
    def check_duplicate_pid(self, pid):
        for process in self.processes:
            if process.pid == pid:
                return process
        return None
