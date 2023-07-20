'''
For Menhir FX
author: Angele Sionneau asionneau@artfx.fr
'''
from threading import Thread
from time import sleep, time
import json
import traceback

from Process import Process, Path, Status
from monitor_utils.config import monitor, mhfx_path
from monitor_utils.windows import get_current_window, get_entity, does_process_exists, get_pid_by_process_name, is_user_afk
from monitor_utils.file import get_data
from monitor_utils.data_management import update_data, push_data, get_processes, push_processes, remove_processes
from monitor_utils.mhfx_log import log

class Monitor(object):
    def __init__(self):
        self.thread = None
        self.wait = monitor.wait_sec
        self.id = str(id(self))
        self.initialize_variables()
    
    def initialize_variables(self):
        self.cycle_incr = 0
        self.processes = {}
        self.is_running = False
        self.last_wait_start = None
        self.other_session_sec = 0
        self.last_process = None
        self.wait_rest = 0.0

    def start_thread(self):
        '''
        Start the monitor thread and monitor.is_running True
        '''
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
        '''
        Stop monitor thread by setting monitor.is_running False
        '''
        try:
            self.manage_processes_data()
            self.initialize_variables()
            self.cycle_incr = 0
        except Exception as e:
            log(traceback.format_exc())
    
    def add_process(self, filename: Path, executable: str, pid: int):
        '''
        Create an object Process and convert it to dict. This dict will be writen in the processes.json file.
        If pid already exists, don't write it and change initial proc infos. 

        :param filename: pathlib.Path
        :param executables: str, from config.monitor.executables
        '''
        try:

            # If it's a new process
            if pid == -1:
                # get the pid
                pid = int(get_pid_by_process_name(executable, self.processes))

            # else it's an existing process
            else:
                # get all processes and write the one with the existing pid to tracker data
                self.processes = get_processes()
                try:
                    self.processes = {str(pid) : self.processes[str(pid)]}
                    if monitor.debug_mode :
                        log(f"pid {pid} already exists in processes: {self.processes}")
                    self.manage_processes_data()

                    # remove old processes with this pid
                    pid_list = [pid,]
                    remove_processes(pid_list)
                    if monitor.debug_mode :
                        log(f"pid {pid} removed from processes.")
                except:
                    if monitor.debug_mode:
                        log(f"For unknown reason, pid doesn't exist in processes.")
                    pid = int(get_pid_by_process_name(executable, self.processes)) 


            # get process of the monitor and update it with new process
            self.processes = get_processes(self.id)
            proc = Process(filename, executable, pid, self.id)
            self.processes.update(proc.as_dict())
            self.last_process = proc.as_dict()
            push_processes(self.processes, self.id)
            if monitor.debug_mode :
                log(f"New process added: {proc.as_dict()}.")
                log(f"Last process updated: {self.last_process}.")

        except:
            log(traceback.format_exc())

    def run(self):
        '''
        The action of the monitor thread.
        Every a certain amount of second : check the foreground window and update the processes accordingly.
        Every cycle: crite processes data in tracker data.
        stop the thread if unused or all the processes are closed.
        '''
        while self.is_running:
            # wait wait_sec seconds
            if monitor.debug_mode:
                log(f'#################  go wait for {self.wait} sec with monitor {self.id} #################')
            sleep(self.wait)
            if monitor.debug_mode:
                log(f'################# Monitor : {self.id} waited #################')

            self.monitor_action()
            
    def monitor_action(self):
        try:
            # check if user is AFK
            if is_user_afk(monitor.user_afk_sec):
                if monitor.debug_mode:
                    log("user is afk")
                self.wait = monitor.wait_sec_afk
                self.last_wait_start = time()
            else:
                self.wait = monitor.wait_sec
                # count how many proc are closed
                self.processes = get_processes(self.id)
                proc_closed = 0
                for pid, infos in self.processes.items():
                    pid = int(pid)
                    if not does_process_exists(pid):
                        self.processes[str(pid)]['status'] = Status.OLD.name
                        proc_closed += 1
                # if all proc closed, sppr processes and stop thread
                if len(self.processes) <= proc_closed:
                        if monitor.debug_mode:
                            log(f'!!!!!!!!!!!!! all the proc are closed for monitor {self.id} !!!!!!!!!!!!!')
                        remove_processes(self.processes.keys())
                        self.stop_thread()
                # elif monitor no longer has a process, stop thread
                elif len(self.processes) == 0:
                    if monitor.debug_mode:
                            log(f"Monitor {self.id} no longer has a process. Stopping monitor thread.")
                    self.stop_thread()
                else:
                    # get current window
                    wndw = get_current_window()
                    window_pid = str(wndw.get('pid'))
                    if monitor.debug_mode:
                        log(f"current window : {wndw.get('pid')} - {wndw.get('title')} - {wndw.get('name')}".encode('ascii', 'ignore').decode('ascii'))
                    
                    # last_wait_start
                    if self.last_wait_start == None:
                        to_add_sec = self.wait
                    else:
                        now = time()
                        delta = now - self.last_wait_start + self.wait_rest
                        to_add_sec = int(delta)
                        self.wait_rest = delta - to_add_sec
                    self.last_wait_start = time()

                    # if current window is monitored, update it
                    if window_pid in self.processes:
                        # if right monitor
                        if self.processes[window_pid].get('monitor_id') == self.id:
                            # update process 
                            self.processes[window_pid]['time'] += to_add_sec
                            self.processes[window_pid]['afk_sec'] = 0
                            self.processes[window_pid]['status'] = Status.ACTIVE.name

                            # update last process
                            self.last_process = {window_pid : self.processes[window_pid]}
                            if monitor.debug_mode:
                                log(f"update this process by adding {to_add_sec} seconds :")
                                log({window_pid: self.processes[window_pid]})
                                log(f'last process updatded')

                            # other session reinitialization
                            self.other_session_sec = 0

                            # push processes
                            push_processes(self.processes, self.id)
                    # else other session add to last session
                    else :
                        if monitor.debug_mode:
                            log(f"current window is not monitored. Add it to last session")
                        
                        # if right monitor
                        monitor_id = next(iter(self.last_process.values()))['monitor_id']
                        if monitor_id == self.id:

                            self.other_session_sec += to_add_sec
                            if not self.other_session_sec >= monitor.max_afk_cycle:
                                last_pid = str(next(iter(self.last_process.keys())))
                                self.processes[last_pid]['time'] += to_add_sec
                                self.processes[last_pid]['status'] = Status.ACTIVE.name
                                push_processes(self.processes, self.id)
                                
                                if monitor.debug_mode:
                                    log(f"last process updated by adding {to_add_sec} seconds :")
                                    log({last_pid: self.processes[last_pid]})

                                    log(f"Other session since {self.other_session_sec} sec.")
                            else:
                                if monitor.debug_mode:
                                    log(f"max_afk_cycle reached for other session")
                    
                    
                    # if cycle complete, write processes data to tracker data
                    self.cycle_incr += to_add_sec
                    if self.cycle_incr >= monitor.total_cycle and self.is_running == True:
                        if monitor.debug_mode:
                            log(f" ~~~~~~~~~~~~~~~~ Cycle complete ~~~~~~~~~~~~~~~~")
                        self.cycle_incr = 0
                        self.manage_processes_data()
                    

        except Exception as e:
            log(f"An exception occurred: {e}")
            log(traceback.format_exc())
             
    def manage_processes_data(self):
        '''
        Execute an action according to the process status.
        Active : Write process data to tracker data.
        Inactive : Manage AFK and write process data to tracker data.
        Old: Manage AFK and remove process data from processes.
        '''
        try:

            # get tracker data and processes data
            data = get_data(mhfx_path.user_data_json)
            processes_copy = self.processes.copy()
            
            log(str(processes_copy.items()))
            # actions
            for pid, infos in processes_copy.items():
                # ACTIVE
                if infos.get('status') == Status.ACTIVE.name:
                    entity = get_entity(infos.get('filename'))
                    data = update_data(data, entity, infos.get('time'), infos.get('first'))
                    self.processes[pid]['status'] = Status.INACTIVE.name
                # OLD
                elif infos.get('status') == Status.OLD.name:
                    if not does_process_exists(int(pid)):
                        entity = get_entity(infos.get('filename'))
                        data = update_data(data, entity, infos.get('time'), infos.get('first'))
                        self.processes.pop(pid)
                # INACTIVE
                else:
                    self.processes[pid]['afk_sec'] += monitor.total_cycle
                    if self.processes[pid]['afk_sec'] >= monitor.max_afk_cycle:
                        entity = get_entity(infos.get('filename'))
                        data = update_data(data, entity, infos.get('time'), infos.get('first'))
                        self.processes[pid]['status'] = Status.OLD.name
                
            # write processes data
            push_processes(self.processes, self.id)

            # write tracker data 
            js_obj = json.dumps(data)
            json_obj = json.dumps(data, indent=4)
            push_data(js_obj, json_obj)

        except Exception as e:
            log(f"An exception occurred: {e}")
            log(traceback.format_exc())

    def check_duplicate_pid(self, pid: int, processes: dict):
        '''
        Check in processes if pid already exists.

        :param pid: int
        :param processes: dict
        :return: bool
        '''
        try:
            for proc_pid in processes.keys():
                proc_pid = int(proc_pid)
                if proc_pid == pid:
                    return True
            return False
        except Exception as e:
            log(traceback.format_exc())

