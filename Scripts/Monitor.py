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
from monitor_utils.data_management import update_data, push_data, get_processes, push_processes, remove_processes, get_last_process, push_last_process
from monitor_utils.mhfx_log import log


class Monitor(object):
    def __init__(self):
        self.thread = None
        self.wait = monitor.wait_sec
        self.id = str(id(self))
        self.initialize_variables()
    
    def initialize_variables(self):
        '''
        Set the variables to initial value.
        '''
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
            processes = get_processes()
            if len(processes) <= 0:
                push_last_process({})
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

            push_last_process(proc.as_dict())
            push_processes(self.processes, self.id)
            if monitor.debug_mode :
                log(f"New process added: {proc.as_dict()}.")
                log(f"Last process updated: {proc.as_dict()}.")

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
            try:
                # wait wait_sec seconds
                if monitor.debug_mode:
                    log(f'#################  go wait for {self.wait} sec with monitor {self.id} #################')
                sleep(self.wait)
                if monitor.debug_mode:
                    log(f'################# Monitor : {self.id} waited #################')

                # check if user is AFK
                if is_user_afk(monitor.user_afk_sec):
                    if monitor.debug_mode:
                        log("user is afk")
                    self.last_wait_start = time()
                    if self.wait == monitor.wait_sec:
                        self.change_last_proc_time(-(monitor.user_afk_sec))
                    self.wait = monitor.wait_sec_afk
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
                                push_last_process(self.last_process)
                                if monitor.debug_mode:
                                    log(f"update this process by adding {to_add_sec} seconds :")
                                    log({window_pid: self.processes[window_pid]})
                                    log(f'last process updated')

                                # other session reinitialization
                                self.other_session_sec = 0

                                # push processes
                                push_processes(self.processes, self.id)
                        # else other session add to last session
                        else :
                            if monitor.debug_mode:
                                log(f"current window is not monitored. Add it to last session")
                            self.change_last_proc_time(to_add_sec)
                        
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
    
    def change_last_proc_time(self, amount):
        '''
        If last process can be modified, update its key "time" by adding the amount in param.

        :param amount: int
        '''
        try:
            self.last_process = get_last_process(self.id)
            if self.last_process != None:
                self.other_session_sec += amount
                if not self.other_session_sec >= monitor.max_afk_cycle:
                    last_pid = str(next(iter(self.last_process.keys())))
                    self.processes[last_pid]['time'] += amount
                    self.processes[last_pid]['status'] = Status.ACTIVE.name
                    push_processes(self.processes, self.id)
                    push_last_process({last_pid: self.processes[last_pid]})
                    
                    if monitor.debug_mode:
                        log(f"last process updated by adding {amount} seconds :")
                        log({last_pid: self.processes[last_pid]})
                        log(f"Other session since {self.other_session_sec} sec.")
                else:
                    if monitor.debug_mode:
                        log(f"max_afk_cycle reached for other session")
            elif monitor.debug_mode:
                log("Not right monitor.")
                self.other_session_sec = 0
        except:
            log(traceback.format_exc()) 
            
    def saveClosedProcess(self, save=True):
        '''
        Get all the processes in tmp file processes.json and remove them if they're closed.
        Save their data before removing them if param save is True.

        :param save: boolean
        '''
        try:
            # get all processes from tmp file
            all_processes = get_processes()
            all_processes_copy = all_processes.copy()
            data = get_data(mhfx_path.user_data_json)
            

            # For all those processes
            for pid, infos in all_processes_copy.items():
                # if process closed, write it to tracker data and remove it from processes list
                if not does_process_exists(pid):
                    entity = get_entity(infos.get('filename'))
                    if entity != None and save==True:
                        if monitor.debug_mode:
                            log(f"Write in tracker data, process {pid} infos.")
                        data = update_data(data, entity, infos.get('time'), infos.get('first'))

                    if monitor.debug_mode:
                        log(f"Remove process {pid} from processes.")
                    all_processes.pop(pid)
            
            # update processes tmp file
            push_processes(all_processes)
            
            # write tracker data 
            if save == True:
                js_obj = json.dumps(data)
                json_obj = json.dumps(data, indent=4)
                push_data(js_obj, json_obj)

        except Exception as e:
            log(f"An exception occurred: {e}")
            log(traceback.format_exc())

    def reinitialise_last_process(self):
        '''
        If the last process is closed, reinitialise the tmp file last_process.json with {}.
        '''
        try:
            last = get_last_process()

            if not does_process_exists(str(next(iter(last.keys())))):
                push_last_process({})
        except Exception as e:
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
            
            # actions
            for pid, infos in processes_copy.items():
                # ACTIVE
                if infos.get('status') == Status.ACTIVE.name:
                    entity = get_entity(infos.get('filename'))
                    if entity != None:
                        data = update_data(data, entity, infos.get('time'), infos.get('first'))
                        self.processes[pid]['status'] = Status.INACTIVE.name
                # OLD
                elif infos.get('status') == Status.OLD.name:
                    if not does_process_exists(int(pid)):
                        entity = get_entity(infos.get('filename'))
                        if entity != None:
                            data = update_data(data, entity, infos.get('time'), infos.get('first'))
                            self.processes.pop(pid)
                # INACTIVE
                else:
                    self.processes[pid]['afk_sec'] += monitor.total_cycle
                    if self.processes[pid]['afk_sec'] >= monitor.max_afk_cycle:
                        entity = get_entity(infos.get('filename'))
                        if entity != None:
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

