from enum import Enum

class Flag(Enum):
    Info = "\033[34m[INFO]\033[0m "
    Debug = "\033[32m[Debug]\033[0m "
    Warn = "\033[33m[Warning]\033[0m "