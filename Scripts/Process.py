from enum import Enum
from pathlib import Path
from datetime import datetime

class Status(Enum):
    ACTIVE = 0
    INACTIVE = 1
    OLD = 2

class Process(object):
    def __init__(self, filename: Path, executable: str, pid: int):
        self.filename = filename
        self.executable = executable
        self.pid = pid
        self.time = 0
        self.status = Status.ACTIVE
        self.afk_sec = 0
        self.first = datetime.now()
    
    def __str__(self):
        return f"Process {str(self.filename)}:\n" \
               f"pid: {self.pid}\n" \
               f"executable: {self.executable}\n" \
               f"time: {self.time}\n" \
               f"status: {str(self.status.name)}\n" \
               f"afk_sec: {self.afk_sec}\n" \
               f"first: {str(self.first)}"
