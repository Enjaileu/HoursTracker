'''
For Menhir FX
author: Angele Sionneau asionneau@artfx.fr
'''

from enum import Enum
from pathlib import Path
from datetime import datetime

class Status(Enum):
    '''
    class Status that represents the status of a process
    Active : The user use the process
    Inactive : The user didn't use the process during the last cycle
    OLD : The process isn't used still a long time
    '''
    ACTIVE = 0
    INACTIVE = 1
    OLD = 2

class Process(object):
    '''
    class Process that represents a process that the monitoring will surveil
    '''
    def __init__(self, filename: Path, executable: str, pid: int, monitor_id: str):
        self.filename = filename
        self.executable = executable
        self.pid = pid
        self.time = 0
        self.status = Status.ACTIVE
        self.afk_sec = 0
        self.first = datetime.now()
        self.monitor_id = monitor_id
    
    def __str__(self):
        return f"Process {str(self.filename)}:\n" \
               f"pid: {self.pid}\n" \
               f"executable: {self.executable}\n" \
               f"time: {self.time}\n" \
               f"status: {str(self.status.name)}\n" \
               f"afk_sec: {self.afk_sec}\n" \
               f"first: {str(self.first)}" \
               f"monitor_id: {str(self.monitor_id)}" 
    
    def as_dict(self):
        return {
            self.pid:{
                "filename": str(self.filename),
                "executable": str(self.executable),
                "time": self.time,
                "status": str(self.status.name),
                "afk_sec": self.afk_sec,
                "first": str(self.first.strftime("%H:%M:%S")),
                "monitor_id": str(self.monitor_id)
            }
        }
