

from enum import Enum

class Status(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class Templates(Enum):
    ESL = "ESL"
    ILAC = "ILAC"
    POST = "POST"
    ACCOUNTING = "ACCOUNTING"
    TEMPLATE_CONFIG_KEY = "populated_templates"
    POP_TEMPLATE_PATH = "./data/populated_templates/"
    ACCOUNT_TEMPLATE_PATH  = "./data/populated_templates/"
# from utils.enums import Status
# Status.RUNNING