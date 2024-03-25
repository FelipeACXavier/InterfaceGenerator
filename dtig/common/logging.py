from os.path import basename
from enum import Enum
from datetime import datetime
from inspect import getframeinfo, stack

class LogLevel(Enum):
  ERROR = 0
  WARNING = 1
  INFO = 2
  DEBUG = 3

def LOG_ERROR(message : str):
  log(LogLevel.ERROR, message)

def LOG_WARNING(message : str):
  log(LogLevel.WARNING, message)

def LOG_INFO(message : str):
  log(LogLevel.INFO, message)

def LOG_DEBUG(message : str):
  log(LogLevel.DEBUG, message)

def printLevel(level : LogLevel) -> str:
  if level == LogLevel.ERROR:
    return "[\033[91mE\033[00m]"
  elif level == LogLevel.WARNING:
    return "[\033[93mW\033[00m]"
  elif level == LogLevel.INFO:
    return "[\033[92mI\033[00m]"
  elif level == LogLevel.DEBUG:
    return "[\033[96mD\033[00m]"

def log(level: LogLevel, message : str) -> None:
  caller = getframeinfo(stack()[2][0])
  print(f"{datetime.now()} {printLevel(level)} {basename(caller.filename)}:{caller.lineno}: {message}")