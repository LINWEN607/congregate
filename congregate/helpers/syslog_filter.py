import logging

class SyslogLevelFilter(logging.Filter):
    def __init__(self, min_syslog_level):
        super().__init__()
        self.min_syslog_level = min_syslog_level
        
        self.python_to_syslog = {
            logging.CRITICAL: 2,  # CRIT
            logging.ERROR: 3,     # ERR
            logging.WARNING: 4,   # WARNING
            logging.INFO: 6,      # INFO
            logging.DEBUG: 7,     # DEBUG
        }
        
        self.syslog_to_python = {v: k for k, v in self.python_to_syslog.items()}
        self.syslog_to_python[0] = 100  # EMERG
        self.syslog_to_python[1] = 90   # ALERT
        self.syslog_to_python[5] = 25   # NOTICE
    
    def filter(self, record):
        if record.levelno in self.python_to_syslog:
            syslog_level = self.python_to_syslog[record.levelno]
        else:
            for python_level in sorted(self.python_to_syslog.keys()):
                if record.levelno >= python_level:
                    closest_std_level = python_level
            syslog_level = self.python_to_syslog.get(closest_std_level, 7)
        
        record.syslog_level = syslog_level
        record.syslog_levelname = logging.getLevelName(syslog_level)
        
        return syslog_level <= self.min_syslog_level